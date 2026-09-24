"""
captcha_solver.py — CAPTCHA detection and automated solving for browser_agent.
===============================================================================
Handles Arkose MatchKey (FunCaptcha) challenges common on X.com.

Architecture:
  detect_challenge_type(page) -> str|None    DOM check, fast, no VLM
  solve_rotation(page, llm)   -> bool        VLM-based rotation solver
  attempt_captcha_solve(page, llm) -> bool   entry point: detect + dispatch

Called from browser_agent.py on_step_start/end hook.

Attempt budget: _MAX_ATTEMPTS per URL. Once budget exhausted the module
silently backs off — control returns to the main agent which can report
failure through its normal completion flow.

Research basis:
  - Halligan et al. (USENIX Security 2025): agentic VLM achieved 70.6% on
    Arkose MatchKey in the wild over 30 days. Primary challenge type: 3D
    object rotation (3d_rollball_objects). Failure mode: coordinate precision.
  - Arkose architecture: BDA fingerprint -> visual challenge -> tguess token.
    tguess is not a problem for real browsers (JS executes natively).
"""

import asyncio
import base64
import json
import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt budget — prevent infinite retry loops
# ---------------------------------------------------------------------------

_MAX_ATTEMPTS = 3

# Keyed by page URL, value = attempt count.
# Cleared when the URL changes (page navigated away from challenge).
_attempt_tracker: dict[str, int] = {}


# ---------------------------------------------------------------------------
# DOM detection — fast, no VLM
# ---------------------------------------------------------------------------

_DETECT_JS = """
() => {
    // Check for Arkose / FunCaptcha iframes (most specific, highest priority)
    const iframes = Array.from(document.querySelectorAll('iframe'));
    for (const f of iframes) {
        const src = f.src || f.getAttribute('src') || '';
        if (src.includes('arkoselabs.com') || src.includes('funcaptcha.com')) {
            return 'arkose_rotation';
        }
        // Arkose-specific ID patterns
        const fid = f.id || '';
        if (fid.includes('arkose') || fid.includes('funcaptcha') ||
                fid === 'FunCaptcha') {
            return 'arkose_rotation';
        }
    }
    // Generic challenge markers (lower specificity)
    const genericSelectors = [
        '[id*="captcha"]',
        '[class*="captcha"]',
        '[data-challenge]',
        '[data-captcha]',
    ];
    for (const sel of genericSelectors) {
        if (document.querySelector(sel)) return 'generic';
    }
    return null;
}
"""


async def detect_challenge_type(page) -> Optional[str]:
    """Check page DOM for CAPTCHA/challenge indicators.

    Returns challenge type string or None if no challenge found.
    DOM-only — no VLM call, designed to be fast on every step.
    """
    try:
        return await page.evaluate(_DETECT_JS)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# VLM interface — image + text -> parsed JSON
# ---------------------------------------------------------------------------

async def _call_llm_with_image(llm, screenshot_bytes: bytes, prompt: str) -> Optional[dict]:
    """Invoke a LangChain-style LLM with a PNG screenshot + text prompt.

    Returns the parsed JSON dict from the response, or None on failure.
    Tries langchain_core first, falls back to langchain.schema.messages.
    """
    b64 = base64.b64encode(screenshot_bytes).decode()

    HumanMessage = None
    for module_path in ("langchain_core.messages", "langchain.schema.messages"):
        try:
            import importlib
            mod = importlib.import_module(module_path)
            HumanMessage = getattr(mod, "HumanMessage", None)
            if HumanMessage:
                break
        except ImportError:
            continue

    if HumanMessage is None:
        log.debug("[CAPTCHA] langchain HumanMessage not importable — solver disabled")
        return None

    try:
        response = await llm.ainvoke([
            HumanMessage(content=[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
                {"type": "text", "text": prompt},
            ])
        ])
        text = response.content if hasattr(response, "content") else str(response)
        # Extract first JSON object from response text
        m = re.search(r"\{[\s\S]+?\}", text)
        if m:
            return json.loads(m.group())
    except Exception as e:
        log.debug(f"[CAPTCHA] LLM call failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Rotation puzzle solver (Arkose 3d_rollball_objects)
# ---------------------------------------------------------------------------

_ROTATION_PROMPT = """You are analyzing a screenshot of an Arkose / FunCaptcha 3D rotation CAPTCHA.

The challenge shows a 3D animal or object. The goal is to rotate it so the animal faces FORWARD with its head pointing UP toward the viewer.

There is a LEFT arrow button and a RIGHT arrow button. Each click rotates the object approximately 45 degrees.

Your task:
1. Identify which direction the animal's head/face currently points (left, right, toward camera, away from camera, down, up, tilted).
2. Find the LEFT arrow button in the image and estimate its center pixel coordinates.
3. Find the RIGHT arrow button in the image and estimate its center pixel coordinates.
4. Determine: to reach the forward-facing position, should you click LEFT or RIGHT, and how many times (1 to 8)?
5. After the rotation, find the Submit / Verify button and estimate its coordinates.

Respond ONLY with a single valid JSON object — no text outside the JSON:
{
  "head_direction": "string describing current orientation",
  "left_btn": [x, y],
  "right_btn": [x, y],
  "click_direction": "left" or "right",
  "click_count": integer 1 to 8,
  "submit_btn": [x, y],
  "reasoning": "one concise sentence"
}

If you cannot determine the orientation clearly, default to: click_direction "right", click_count 2.
If you cannot find a button, use [0, 0] for its coordinates.
"""


async def solve_rotation(page, llm) -> bool:
    """Attempt to solve a rotation CAPTCHA on the current page.

    Workflow:
      1. Screenshot the full page (includes the Arkose overlay).
      2. Ask VLM: orientation + button coordinates + submit location.
      3. Click the arrow the requested number of times.
      4. Click Submit.
    Returns True if clicks were executed, False on any failure.
    """
    try:
        screenshot = await page.screenshot(type="png")
    except Exception as e:
        log.debug(f"[CAPTCHA] Screenshot failed: {e}")
        return False

    result = await _call_llm_with_image(llm, screenshot, _ROTATION_PROMPT)
    if not result:
        log.debug("[CAPTCHA] VLM returned no parseable result for rotation puzzle")
        return False

    direction = str(result.get("click_direction", "right")).lower().strip()
    if direction not in ("left", "right"):
        direction = "right"
    clicks = max(1, min(8, int(result.get("click_count", 2) or 2)))

    log.info(
        f"[CAPTCHA] Rotation solver: head={result.get('head_direction')} "
        f"-> click {direction} x{clicks}. Reason: {result.get('reasoning')}"
    )

    # --- Arrow clicking -------------------------------------------------------
    btn_key = "left_btn" if direction == "left" else "right_btn"
    btn_coords = result.get(btn_key)
    clicked = 0

    if btn_coords and len(btn_coords) == 2 and (btn_coords[0] or btn_coords[1]):
        x, y = int(btn_coords[0]), int(btn_coords[1])
        for i in range(clicks):
            try:
                await page.mouse.click(x, y)
                await asyncio.sleep(0.35)
                clicked += 1
            except Exception as e:
                log.debug(f"[CAPTCHA] Arrow click {i+1}/{clicks} failed: {e}")
                break
    else:
        # Fallback: try DOM selectors in each page frame
        arrow_selectors = {
            "left": [
                '[aria-label*="left" i]',
                '.challenge-button-left',
                'button.rotate-left',
            ],
            "right": [
                '[aria-label*="right" i]',
                '.challenge-button-right',
                'button.rotate-right',
            ],
        }
        for frame in page.frames:
            frame_url = frame.url or ""
            if "arkose" not in frame_url and "funcaptcha" not in frame_url:
                continue
            for sel in arrow_selectors.get(direction, []):
                try:
                    btn = await frame.query_selector(sel)
                    if btn:
                        for _ in range(clicks):
                            await btn.click()
                            await asyncio.sleep(0.35)
                            clicked += 1
                        break
                except Exception:
                    continue
            if clicked:
                break

    if not clicked:
        log.debug("[CAPTCHA] No arrow button found via coordinates or DOM selectors")
        return False

    # --- Short pause to let challenge animate --------------------------------
    await asyncio.sleep(0.8)

    # --- Submit --------------------------------------------------------------
    submit_coords = result.get("submit_btn")
    if submit_coords and len(submit_coords) == 2 and (submit_coords[0] or submit_coords[1]):
        sx, sy = int(submit_coords[0]), int(submit_coords[1])
        try:
            await page.mouse.click(sx, sy)
            await asyncio.sleep(0.5)
            log.info("[CAPTCHA] Submit button clicked")
        except Exception as e:
            log.debug(f"[CAPTCHA] Submit click failed: {e}")
    else:
        # Try generic submit selectors across frames
        submit_selectors = [
            'button[type="submit"]',
            '[aria-label*="submit" i]',
            '[aria-label*="verify" i]',
            'button.verify-button',
            'button.submit-button',
            'input[type="submit"]',
        ]
        for frame in ([page] + page.frames):
            for sel in submit_selectors:
                try:
                    btn = await frame.query_selector(sel)
                    if btn:
                        await btn.click()
                        await asyncio.sleep(0.5)
                        log.info(f"[CAPTCHA] Submit via selector '{sel}'")
                        break
                except Exception:
                    continue

    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def attempt_captcha_solve(page, llm) -> bool:
    """Detect and attempt to solve any CAPTCHA present on the current page.

    Lightweight — the DOM detection runs on every step and returns quickly
    when no challenge is present. The VLM is only invoked when a challenge
    is detected.

    Returns True if a solve was attempted, False if no challenge found or
    attempt budget exhausted.
    """
    try:
        url = page.url or ""
    except Exception:
        return False

    # Check attempt budget for this URL
    attempts = _attempt_tracker.get(url, 0)
    if attempts >= _MAX_ATTEMPTS:
        return False

    challenge_type = await detect_challenge_type(page)
    if not challenge_type:
        # No challenge — clear counter if URL matches a previous challenge URL
        if url in _attempt_tracker:
            del _attempt_tracker[url]
        return False

    # Increment attempt counter
    _attempt_tracker[url] = attempts + 1
    log.info(
        f"[CAPTCHA] Challenge detected: type={challenge_type} "
        f"url={url[:80]} attempt={attempts + 1}/{_MAX_ATTEMPTS}"
    )

    if challenge_type == "arkose_rotation":
        return await solve_rotation(page, llm)

    # No solver for generic/unknown challenge types yet
    log.info(f"[CAPTCHA] No solver for type '{challenge_type}' — relying on agent prompt guidance")
    return False
