---
name: ui_reference_capture
description: "Use this skill when the user wants to capture UI/UX design patterns from a website for the reference library. Triggers: 'capture the UI from', 'extract design tokens from', 'add to the UI reference library', 'analyze how [site] looks', 'extract the design system from'. Produces docs/ui_references/{site_name}/notes.md and tokens.css. Requires a URL. Two modes: CSS-only (no browser needed) and full mode (screenshot + vision analysis via qwen3-vl-4b-instruct)."
---

# Skill: UI Reference Capture

## What This Does

Captures design tokens and qualitative UI/UX analysis from a live website. Produces two files:
- `docs/ui_references/{site_name}/notes.md` — qualitative analysis: what makes it feel good, what ports to Exocortex, what doesn't
- `docs/ui_references/{site_name}/tokens.css` — raw CSS custom properties and extracted values

## Inputs Required

- **URL** — full URL including scheme (https://...)
- **Site name** — short identifier used as the directory name (e.g., `opengridworks`, `linear`, `vercel`)
- **Mode** — `full` (default, requires vision model) or `css-only` (token extraction only, no screenshot/vision)

If the user provides a URL but no site name, derive it from the domain (strip www., use first segment).

---

## Phase 1: Extract CSS and DOM Structure

Run the following Python in `code_execution_tool`. This is the foundation — runs in both modes.

```python
import requests
import re
import json
import base64
from urllib.parse import urljoin, urlparse
from pathlib import Path

TARGET_URL = "REPLACE_WITH_URL"
OUTPUT_DIR = Path("/a0/usr/Exocortex/docs/ui_references/REPLACE_WITH_SITE_NAME")
VISION_URL = "http://host.docker.internal:1234/v1"
VISION_MODEL = "qwen3-vl-4b-instruct"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"[UI-CAP] Fetching {TARGET_URL}")

# ── Fetch HTML ────────────────────────────────────────────────────────────────
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
try:
    resp = requests.get(TARGET_URL, headers=headers, timeout=20)
    html = resp.text
    print(f"[UI-CAP] HTML fetched: {len(html):,} bytes")
except Exception as e:
    print(f"[UI-CAP] Fetch failed: {e}")
    html = ""

# ── Collect all CSS ───────────────────────────────────────────────────────────
css_chunks = []

# Inline <style> blocks
style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
for block in style_blocks:
    css_chunks.append(block)

# External stylesheets
sheet_urls = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
sheet_urls += re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\']', html, re.IGNORECASE)
print(f"[UI-CAP] Found {len(sheet_urls)} external stylesheets")

for sheet_url in sheet_urls[:8]:  # cap at 8 sheets
    full_url = urljoin(TARGET_URL, sheet_url)
    try:
        sheet_resp = requests.get(full_url, headers=headers, timeout=15)
        css_chunks.append(sheet_resp.text)
        print(f"[UI-CAP]   Sheet: {len(sheet_resp.text):,} bytes — {full_url[:80]}")
    except Exception as e:
        print(f"[UI-CAP]   Sheet failed: {full_url[:60]} — {e}")

full_css = "\n".join(css_chunks)
print(f"[UI-CAP] Total CSS: {len(full_css):,} chars across {len(css_chunks)} sources")

# ── The 9-Grep methodology ─────────────────────────────────────────────────────
# Each pattern surfaces a specific design token category

def grep_css(pattern, css, label, limit=40):
    matches = re.findall(pattern, css)
    unique = list(dict.fromkeys(matches))[:limit]
    print(f"[UI-CAP] {label}: {len(unique)} unique matches")
    return unique

results = {}

# 1. CSS custom properties (--var: value)
props = re.findall(r'(--[\w-]+)\s*:\s*([^;}{]+)', full_css)
prop_dict = {}
for k, v in props:
    prop_dict[k] = v.strip()
print(f"[UI-CAP] CSS variables: {len(prop_dict)} unique")
results["css_variables"] = prop_dict

# 2. Transitions
results["transitions"] = grep_css(r'transition\s*:\s*[^;{]+', full_css, "transitions")

# 3. Easing curves
results["easings"] = grep_css(r'cubic-bezier\([^)]+\)', full_css, "easings")

# 4. Backdrop filters
results["backdrop_filters"] = grep_css(r'backdrop-filter\s*:\s*[^;{]+', full_css, "backdrop-filters")

# 5. Hover states (property + value patterns)
results["hover_states"] = grep_css(r':hover\s*\{([^}]+)\}', full_css, "hover-states")

# 6. Animations / keyframes
results["keyframes"] = grep_css(r'@keyframes\s+([\w-]+)', full_css, "keyframes")

# 7. Font families
results["fonts"] = grep_css(r'font-family\s*:\s*([^;{]+)', full_css, "fonts")

# 8. Box shadows
results["shadows"] = grep_css(r'box-shadow\s*:\s*[^;{]+', full_css, "shadows")

# 9. Color patterns — HSL, hex, oklch
results["colors_hsl"] = grep_css(r'hsl\([^)]+\)', full_css, "hsl-colors")
results["colors_hex"] = grep_css(r'#[0-9A-Fa-f]{3,8}\b', full_css, "hex-colors")
results["colors_oklch"] = grep_css(r'oklch\([^)]+\)', full_css, "oklch-colors")

# ── Serialize results ─────────────────────────────────────────────────────────
results_path = OUTPUT_DIR / "extraction.json"
with open(results_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"[UI-CAP] Extraction saved: {results_path}")

# ── Print token summary for review ───────────────────────────────────────────
print("\n=== CSS VARIABLES SAMPLE (first 30) ===")
for k, v in list(prop_dict.items())[:30]:
    print(f"  {k}: {v}")

print(f"\n=== TRANSITIONS ({len(results['transitions'])} found) ===")
for t in results["transitions"][:10]:
    print(f"  {t[:120]}")

print(f"\n=== FONTS ===")
for f in results["fonts"][:6]:
    print(f"  {f[:120]}")

print(f"\n=== SHADOWS ===")
for s in results["shadows"][:6]:
    print(f"  {s[:120]}")

print("\n[UI-CAP] Phase 1 complete.")
```

After Phase 1, review the output. The key data is in `extraction.json`. Proceed to Phase 2 for the screenshot, or skip to Phase 3 (write tokens) if running in CSS-only mode.

---

## Phase 2: Screenshot + Vision Analysis (Full Mode Only)

Run the following Python to take a screenshot using Playwright (patchright) and call the vision model.

```python
import asyncio
import base64
import json
import requests
from pathlib import Path

TARGET_URL = "REPLACE_WITH_URL"
OUTPUT_DIR = Path("/a0/usr/Exocortex/docs/ui_references/REPLACE_WITH_SITE_NAME")
VISION_URL = "http://host.docker.internal:1234/v1"
VISION_MODEL = "qwen3-vl-4b-instruct"

SCREENSHOT_PATH = OUTPUT_DIR / "screenshot.png"

# ── Take screenshot ───────────────────────────────────────────────────────────
async def take_screenshot():
    try:
        from patchright.async_api import async_playwright
        print("[UI-CAP] Using patchright for screenshot")
    except ImportError:
        from playwright.async_api import async_playwright
        print("[UI-CAP] Using playwright for screenshot")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        except Exception:
            # Some pages never reach networkidle — take what we have
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=20000)
        # Wait briefly for any CSS animations to settle
        await asyncio.sleep(2)
        await page.screenshot(path=str(SCREENSHOT_PATH), full_page=False)
        await browser.close()
    print(f"[UI-CAP] Screenshot saved: {SCREENSHOT_PATH}")

asyncio.run(take_screenshot())

# ── Encode screenshot ─────────────────────────────────────────────────────────
with open(SCREENSHOT_PATH, "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()
print(f"[UI-CAP] Screenshot encoded: {len(image_b64):,} chars")

# ── Call vision model — qualitative analysis ──────────────────────────────────
VISUAL_PROMPTS = [
    {
        "label": "overall_impression",
        "question": (
            "Look at this website screenshot. Describe in 3-4 sentences what makes it feel good "
            "(or not). Focus on: visual weight, spacing rhythm, color temperature, motion cues you "
            "can infer from hover states or active indicators, and the overall emotional register "
            "(calm/energetic/authoritative/playful). Be specific about what you actually see."
        )
    },
    {
        "label": "color_strategy",
        "question": (
            "Analyze the color strategy in this screenshot. What is the background palette? "
            "What are the accent colors and where are they used? How does color signal state changes "
            "(hover, active, selected, error, success)? What temperature is the overall palette "
            "(warm/cool/neutral) and what mood does it create?"
        )
    },
    {
        "label": "typography_hierarchy",
        "question": (
            "Describe the typographic hierarchy in this screenshot. How many distinct text levels "
            "are visible? What's the relationship between the largest and smallest text? "
            "Is the type system high-contrast (many weights/sizes) or compressed (small range)? "
            "What font category appears to be in use (geometric sans, humanist, monospace, serif)?"
        )
    },
    {
        "label": "spatial_rhythm",
        "question": (
            "Analyze the spatial rhythm and layout density of this screenshot. Is it spacious or "
            "compact? Are there clear grid lines or does content feel organic? "
            "How do cards or panels relate to each other — tight grid, loose masonry, or list-based? "
            "Name one specific spacing pattern that appears to repeat."
        )
    },
    {
        "label": "interaction_signals",
        "question": (
            "What interaction affordances are visible in this screenshot? Look for: buttons with "
            "clear hover/active visual styling, cursor changes you can infer, focus rings, "
            "tooltips or helper text, loading or progress indicators, and any animation cues "
            "(fade edges, transition previews). What tells you something is clickable?"
        )
    }
]

vision_results = {}
base_headers = {"Content-Type": "application/json"}

for prompt_item in VISUAL_PROMPTS:
    label = prompt_item["label"]
    question = prompt_item["question"]
    print(f"[UI-CAP] Vision query: {label}")

    payload = {
        "model": VISION_MODEL,
        "max_tokens": 400,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ]
    }
    try:
        r = requests.post(
            f"{VISION_URL}/chat/completions",
            headers=base_headers,
            json=payload,
            timeout=60
        )
        r.raise_for_status()
        answer = r.json()["choices"][0]["message"]["content"].strip()
        vision_results[label] = answer
        print(f"[UI-CAP]   {label}: {len(answer)} chars")
    except Exception as e:
        vision_results[label] = f"[error: {e}]"
        print(f"[UI-CAP]   {label}: FAILED — {e}")

# Save vision results
vision_path = OUTPUT_DIR / "vision_analysis.json"
with open(vision_path, "w") as f:
    json.dump(vision_results, f, indent=2)
print(f"\n[UI-CAP] Vision analysis saved: {vision_path}")

# Print for review
for label, text in vision_results.items():
    print(f"\n=== {label.upper()} ===")
    print(text[:600])
```

Review the vision output. The 5 dimensions give you the qualitative foundation for notes.md.

---

## Phase 3: Write tokens.css

Based on the `extraction.json` data, write `tokens.css`. This is the raw token file — preserve values exactly as extracted from the source.

```python
import json
from pathlib import Path
from datetime import date

OUTPUT_DIR = Path("/a0/usr/Exocortex/docs/ui_references/REPLACE_WITH_SITE_NAME")
TARGET_URL = "REPLACE_WITH_URL"
SITE_NAME = "REPLACE_WITH_SITE_NAME"

with open(OUTPUT_DIR / "extraction.json") as f:
    data = json.load(f)

css_vars = data.get("css_variables", {})
transitions = data.get("transitions", [])
easings = data.get("easings", [])
fonts = data.get("fonts", [])
shadows = data.get("shadows", [])
keyframes = data.get("keyframes", [])

today = date.today().isoformat()

# Group CSS variables by common prefix patterns
groups = {}
ungrouped = {}
for k, v in css_vars.items():
    # Find prefix: --color-, --space-, --font-, etc.
    parts = k.lstrip("-").split("-")
    prefix = parts[0] if len(parts) > 1 else "misc"
    groups.setdefault(prefix, {})[k] = v

# Build the CSS file
lines = [
    f"/* {'=' * 60}",
    f" * {SITE_NAME.title()} Design Tokens",
    f" * Source: {TARGET_URL}",
    f" * Extracted: {today}",
    f" *",
    f" * RAW EXTRACT — do not edit values here.",
    f" * Curated adaptations belong in docs/ui_references/exocortex.css",
    f" * {'=' * 60} */",
    "",
    ":root {",
    ""
]

# Custom properties grouped
for prefix, props in sorted(groups.items()):
    lines.append(f"  /* ---------- {prefix.title()} ---------- */")
    for k, v in sorted(props.items()):
        lines.append(f"  {k}: {v};")
    lines.append("")

lines.append("}")
lines.append("")

# Transitions section
if transitions:
    lines.append("/* ---- Observed Transition Patterns ---- */")
    for t in transitions[:15]:
        lines.append(f"/* transition: {t[:120]} */")
    lines.append("")

# Easing section
if easings:
    lines.append("/* ---- Observed Easing Curves ---- */")
    unique_easings = list(dict.fromkeys(easings))
    for e in unique_easings[:10]:
        lines.append(f"/* {e} */")
    lines.append("")

# Shadows section
if shadows:
    lines.append("/* ---- Observed Shadows ---- */")
    for s in shadows[:10]:
        lines.append(f"/* box-shadow: {s[:120]} */")
    lines.append("")

# Keyframes section
if keyframes:
    lines.append("/* ---- Observed Animations ---- */")
    for k in keyframes[:10]:
        lines.append(f"/* @keyframes {k} */")
    lines.append("")

tokens_content = "\n".join(lines)
tokens_path = OUTPUT_DIR / "tokens.css"
tokens_path.write_text(tokens_content, encoding="utf-8")
print(f"[UI-CAP] Wrote {len(lines)} lines to {tokens_path}")
print(f"[UI-CAP] {len(css_vars)} CSS variables, {len(transitions)} transitions, {len(shadows)} shadows")
```

---

## Phase 4: Write notes.md

Synthesize the extraction data and vision analysis into `notes.md`. Write this yourself — the notes file requires your judgment, not just data dump.

**Structure to follow (based on established format in this library):**

```markdown
# {Site Display Name} — UI reference notes

**URL:** {TARGET_URL}
**Tagline:** "{tagline if visible in the page title or hero}"
**Domain:** {what kind of site/product this is — one sentence}
**Tech:** {detected framework clues from CSS class naming, custom property prefixes, or JS framework}
**Captured:** {today's date}

## What makes it feel good

{3-5 compounding design decisions that create the overall quality impression.
Numbered list in descending order of visual/experiential impact.
Each item: bold pattern name + explanation of what it does and why it works.
Ground each in specific values or behaviors from the extraction data.}

## Information conveyance

{How the design communicates structure and state.
Bullet list. Focus on: information hierarchy, density patterns, state signaling,
navigation affordances, data presentation conventions.}

## What ports cleanly to Exocortex

{Specific patterns from this site that directly apply to the Exocortex UI.
Be concrete — not "nice typography" but "small-caps section headers with 0.08em letter-spacing."
For each: one sentence on what to apply and one sentence on where.}

## What does NOT port

{Patterns that look good here but don't belong in Exocortex.
Each with a specific reason — domain mismatch, visual vocabulary conflict, technical constraint.}

## Extraction methodology used

{Brief bullet list of what tools/approaches produced this capture.
Include: how many CSS files, whether vision analysis was run, whether Playwright was used.}

## Caveats

{Honest assessment of what might be missing or unreliable in this capture.
E.g., SPA routes not captured, dark mode only, runtime-injected classes not extracted.}
```

**Critical writing rules for notes.md:**
- Ground every claim in extracted data. "80ms transitions" not "fast transitions."
- The "what makes it feel good" section requires the vision analysis. Don't write it from CSS alone.
- "What ports cleanly" must reference Exocortex specifically — what component, what context.
- Be precise about what you extracted vs. what you inferred from screenshots vs. what you're guessing.

---

## Phase 5: Cleanup and Summary

After writing both files:

1. Remove the temporary `extraction.json` and `vision_analysis.json` from the output dir (they're intermediate artifacts, not reference material)
2. Report what was captured: CSS variable count, transition count, vision analysis status, file locations
3. Mention any gaps: SPA routes not captured, JS-injected styles missed, vision model failures

```python
from pathlib import Path

OUTPUT_DIR = Path("/a0/usr/Exocortex/docs/ui_references/REPLACE_WITH_SITE_NAME")

# Remove intermediate files
for f in ["extraction.json", "vision_analysis.json"]:
    p = OUTPUT_DIR / f
    if p.exists():
        p.unlink()
        print(f"[UI-CAP] Cleaned: {f}")

# Report final outputs
for f in OUTPUT_DIR.iterdir():
    print(f"[UI-CAP] Output: {f.name} ({f.stat().st_size:,} bytes)")
```

---

## CSS-Only Mode (Fallback)

If the vision model is unavailable or the user requests CSS-only mode:
- Skip Phase 2 entirely
- In Phase 4 (notes.md), mark the "What makes it feel good" section as `[Vision analysis not available — populated from CSS data only]`
- Still write the full tokens.css and notes.md — just note the limitation in the Caveats section

To test if the vision model is reachable before starting:
```python
import requests
try:
    r = requests.get("http://host.docker.internal:1234/v1/models", timeout=5)
    models = [m["id"] for m in r.json().get("data", [])]
    vision_ok = "qwen3-vl-4b-instruct" in models
    print(f"[UI-CAP] Vision model: {'available' if vision_ok else 'NOT FOUND'}")
    print(f"[UI-CAP] Available models: {models}")
except Exception as e:
    print(f"[UI-CAP] LM Studio unreachable: {e}")
    vision_ok = False
```

---

## Quality Checks

- [ ] `tokens.css` has at least 5 CSS custom properties (if the site uses them) OR at least 3 observed patterns in comments
- [ ] `notes.md` "What makes it feel good" section has 3+ numbered items with specific values
- [ ] Every claim in notes.md that references a specific value (timing, color, radius) cites the actual value
- [ ] "What ports to Exocortex" is concrete — names a component or context, not abstract advice
- [ ] If vision failed, the notes.md Caveats section says so explicitly

## Anti-Patterns

- **Writing notes.md from CSS variables alone without describing what they look like.** CSS variables tell you the values; the vision model tells you what they achieve visually. Both are needed.
- **Overclaiming from partial CSS capture.** SPAs inject most styles at runtime — static CSS fetch will miss component styles. Note the limitation.
- **Copying all 200 CSS variables without grouping.** The tokens.css should be organized by category with comments. Raw dumps are unreadable.
- **Generic notes.** "Clean typography and good spacing" is useless. "16px base size with 1.5 line-height on a 13px body creates breathing room without wasting vertical space" is useful.
- **Forgetting the output directory.** Always write to `/a0/usr/Exocortex/docs/ui_references/{site_name}/`. Not to `/a0/work/` or anywhere temporary.
