import asyncio
import math as _math
import random as _random
import time
from typing import Optional, cast
from agent import Agent, InterventionException
from pathlib import Path

from python.helpers.tool import Tool, Response
from python.helpers import files, defer, persist_chat, strings

# ---------------------------------------------------------------------------
# Patchright: replace playwright.async_api before browser_use imports it.
# Removes Runtime.enable CDP leak + AutomationControlled flag — the primary
# signals that betray Playwright-based automation to bot detectors.
# ---------------------------------------------------------------------------
import sys as _sys
try:
    if 'playwright.async_api' not in _sys.modules:
        import patchright.async_api as _pr_async
        _sys.modules['playwright.async_api'] = _pr_async
        del _pr_async
except ImportError:
    pass
del _sys

from python.helpers.browser_use import browser_use  # type: ignore[attr-defined]
from python.helpers.print_style import PrintStyle
from python.helpers.playwright import ensure_playwright_binary
from python.helpers.secrets import get_secrets_manager
from python.extensions.message_loop_start._10_iteration_no import get_iter_no
from pydantic import BaseModel
import uuid
from python.helpers.dirty_json import DirtyJson


# ---------------------------------------------------------------------------
# Human-like cursor movement — pure Python, no external dependencies.
# Based on cubic Bézier with randomly offset control points (same side →
# single arc, not S-curve) and Fitts's Law pacing.
# ---------------------------------------------------------------------------

def _bezier_path(x0: float, y0: float, x1: float, y1: float, n_steps: int = 12) -> list:
    """Return list of (x, y) ints along a Bézier curve from (x0,y0) to (x1,y1)."""
    dx, dy = x1 - x0, y1 - y0
    dist = _math.sqrt(dx * dx + dy * dy) or 1.0
    px, py = -dy / dist, dx / dist                     # perpendicular unit vector
    side = _random.choice([-1, 1])
    sigma = dist * 0.03
    o1 = dist * _random.uniform(0.10, 0.25) * side
    o2 = dist * _random.uniform(0.10, 0.25) * side
    cp1x = x0 + dx * 0.25 + px * o1 + _random.gauss(0, sigma)
    cp1y = y0 + dy * 0.25 + py * o1 + _random.gauss(0, sigma)
    cp2x = x0 + dx * 0.75 + px * o2 + _random.gauss(0, sigma)
    cp2y = y0 + dy * 0.75 + py * o2 + _random.gauss(0, sigma)
    pts = []
    for i in range(n_steps + 1):
        t = i / n_steps
        x = (1-t)**3*x0 + 3*(1-t)**2*t*cp1x + 3*(1-t)*t**2*cp2x + t**3*x1
        y = (1-t)**3*y0 + 3*(1-t)**2*t*cp1y + 3*(1-t)*t**2*cp2y + t**3*y1
        pts.append((int(x), int(y)))
    return pts


async def _mouse_move_bezier(page, x1: int, y1: int, x0: int | None = None, y0: int | None = None) -> None:
    """Move mouse from (x0,y0) -> (x1,y1) along a Bezier curve.

    Fitts's Law coefficients calibrated from dejanseo/mouse_movement_tracking
    (685k real human events, 1991 sessions):
      - Median speed: 0.33 px/ms  -> scale = 3.05 ms/px
      - 100px: ~314ms, 400px: ~1230ms, 800px: ~2450ms
      - Inter-event poll: 16ms (60Hz browser mousemove batching)
    """
    vs = page.viewport_size
    if x0 is None:
        x0 = (vs.get('width', 1024) // 2) if vs else 512
    if y0 is None:
        y0 = (vs.get('height', 2048) // 4) if vs else 512
    dist = _math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
    # Calibrated Fitts's Law: base=9ms + scale=3.05ms/px, capped 150ms–2500ms
    # Added gaussian jitter (std=15%) to avoid mechanical regularity
    raw_duration_ms = 9.0 + 3.05 * dist
    jitter = _random.gauss(1.0, 0.15)
    duration_ms = max(150.0, min(2500.0, raw_duration_ms * jitter))
    duration_s = duration_ms / 1000.0
    # Step count: ~16ms per intermediate point (browser mousemove rate)
    n_steps = max(6, int(duration_ms / 16))
    pts = _bezier_path(x0, y0, x1, y1, n_steps)
    step_delay = duration_s / max(len(pts) - 1, 1)
    for px, py in pts[1:]:
        await page.mouse.move(px, py)
        await asyncio.sleep(step_delay)


class State:
    @staticmethod
    async def create(agent: Agent):
        state = State(agent)
        return state

    def __init__(self, agent: Agent):
        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.task: Optional[defer.DeferredTask] = None
        self.use_agent: Optional[browser_use.Agent] = None
        self.secrets_dict: Optional[dict[str, str]] = None
        self.iter_no = 0

    def __del__(self):
        self.kill_task()
        files.delete_dir(self.get_user_data_dir()) # cleanup user data dir

    def get_user_data_dir(self):
        return str(
            Path.home()
            / ".config"
            / "browseruse"
            / "profiles"
            / f"agent_{self.agent.context.id}"
        )

    async def _initialize(self):
        if self.browser_session:
            return

        # for some reason we need to provide exact path to headless shell, otherwise it looks for headed browser
        pw_binary = ensure_playwright_binary()

        self.browser_session = browser_use.BrowserSession(
            browser_profile=browser_use.BrowserProfile(
                headless=True,
                disable_security=True,
                chromium_sandbox=False,
                accept_downloads=True,
                downloads_path=files.get_abs_path("usr/downloads"),
                allowed_domains=["*", "http://*", "https://*"],
                executable_path=pw_binary,
                keep_alive=True,
                minimum_wait_page_load_time=1.0,
                wait_for_network_idle_page_load_time=2.0,
                maximum_wait_page_load_time=10.0,
                window_size={"width": 1024, "height": 2048},
                screen={"width": 1024, "height": 2048},
                viewport={"width": 1024, "height": 2048},
                no_viewport=False,
                args=["--headless=new"],
                # Use a unique user data directory to avoid conflicts
                user_data_dir=self.get_user_data_dir(),
                extra_http_headers=self.agent.config.browser_http_headers or {},
                )
        )

        await self.browser_session.start() if self.browser_session else None
        # self.override_hooks()

        # --------------------------------------------------------------------------
        # Patch to enforce vertical viewport size
        # --------------------------------------------------------------------------
        # Browser-use auto-configuration overrides viewport settings, causing wrong
        # aspect ratio. We fix this by directly setting viewport size after startup.
        # --------------------------------------------------------------------------

        if self.browser_session:
            try:
                page = await self.browser_session.get_current_page()
                if page:
                    await page.set_viewport_size({"width": 1024, "height": 2048})
            except Exception as e:
                PrintStyle().warning(f"Could not force set viewport size: {e}")

        # --------------------------------------------------------------------------

        # Apply stealth evasions to the browser context so all pages avoid
        # headless browser fingerprinting (navigator.webdriver, Chrome runtime, etc).
        # playwright-stealth 2.x applies init scripts to the context, covering every
        # page created within the session automatically.
        if self.browser_session and self.browser_session.browser_context:
            try:
                from playwright_stealth import Stealth
                await Stealth(
                    navigator_user_agent_override=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    ),
                    navigator_platform_override="Win32",
                ).apply_stealth_async(self.browser_session.browser_context)
            except Exception as e:
                PrintStyle().warning(f"[BROWSER] Stealth init failed (non-fatal): {e}")

        # Add init scripts to the browser session
        if self.browser_session and self.browser_session.browser_context:
            js_override = files.get_abs_path("lib/browser/init_override.js")
            await self.browser_session.browser_context.add_init_script(path=js_override) if self.browser_session else None
            # Scroll humanizer — ±8% variance on scrollBy/scrollTo
            try:
                import os as _os
                js_humanize = files.get_abs_path("lib/browser/humanize_scroll.js")
                if _os.path.exists(js_humanize):
                    await self.browser_session.browser_context.add_init_script(path=js_humanize)
            except Exception:
                pass

    def start_task(self, task: str):
        if self.task and self.task.is_alive():
            self.kill_task()

        self.task = defer.DeferredTask(
            thread_name="BrowserAgent" + self.agent.context.id
        )
        if self.agent.context.task:
            self.agent.context.task.add_child_task(self.task, terminate_thread=True)
        self.task.start_task(self._run_task, task) if self.task else None
        return self.task

    def kill_task(self):
        if self.task:
            # Close the browser session on the task's own event loop BEFORE terminating
            # the thread. Playwright's CDP callbacks are bound to the worker loop — if we
            # kill the thread first and then try to close from a new loop, those callbacks
            # call loop.call_soon() on a closed loop, producing a cascade of
            # "RuntimeError: Event loop is closed" errors.
            loop = getattr(self.task.event_loop_thread, 'loop', None)
            if self.browser_session and loop and loop.is_running():
                try:
                    session = self.browser_session
                    self.browser_session = None  # Clear now to prevent double-close below
                    close_future = asyncio.run_coroutine_threadsafe(
                        State._close_session_safe(session), loop
                    )
                    close_future.result(timeout=10.0)
                except Exception:
                    pass
            self.task.kill(terminate_thread=True)
            self.task = None
        if self.browser_session:
            # Fallback: no live task thread, close with a temporary event loop
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(State._close_session_safe(self.browser_session))
                loop.close()
            except Exception as e:
                PrintStyle().error(f"Error closing browser session: {e}")
            finally:
                self.browser_session = None
        self.use_agent = None
        self.iter_no = 0

    @staticmethod
    async def _close_session_safe(session) -> None:
        """Close a BrowserSession, swallowing all exceptions."""
        try:
            await session.close()
        except Exception:
            pass

    async def _run_task(self, task: str):
        await self._initialize()

        class DoneResult(BaseModel):
            title: str
            response: str
            page_summary: str

        # Initialize controller
        controller = browser_use.Controller(output_model=DoneResult)

        # Register custom completion action with proper ActionResult fields
        @controller.registry.action("Complete task", param_model=DoneResult)
        async def complete_task(params: DoneResult):
            result = browser_use.ActionResult(
                is_done=True, success=True, extracted_content=params.model_dump_json()
            )
            return result

        model = self.agent.get_browser_model()

        try:

            secrets_manager = get_secrets_manager(self.agent.context)
            secrets_dict = secrets_manager.load_secrets()

            self.use_agent = browser_use.Agent(
                task=task,
                browser_session=self.browser_session,
                llm=model,
                use_vision=self.agent.config.browser_model.vision,
                extend_system_message=self.agent.read_prompt(
                    "prompts/browser_agent.system.md"
                ),
                controller=controller,
                enable_memory=False,  # Disable memory to avoid state conflicts
                llm_timeout=3000, # TODO rem
                sensitive_data=cast(dict[str, str | dict[str, str]] | None, secrets_dict or {}),  # Pass secrets
            )
        except Exception as e:
            raise Exception(
                f"Browser agent initialization failed. This might be due to model compatibility issues. Error: {e}"
            ) from e

        self.iter_no = get_iter_no(self.agent)

        async def hook(agent: browser_use.Agent):
            await self.agent.wait_if_paused()
            if self.iter_no != get_iter_no(self.agent):
                raise InterventionException("Task cancelled")
            # CAPTCHA detection + solving — lightweight DOM check every step,
            # VLM solver only fires when a challenge is detected.
            try:
                if agent.browser_session:
                    page = await agent.browser_session.get_current_page()
                    if page:
                        from python.tools.captcha_solver import attempt_captcha_solve
                        await attempt_captcha_solve(page, model)
            except Exception:
                pass
            # ~20% chance: idle Bézier mouse jitter so cursor isn't frozen between steps
            if _random.random() < 0.20:
                try:
                    if agent.browser_session:
                        page = await agent.browser_session.get_current_page()
                        if page:
                            vs = page.viewport_size
                            w = vs.get('width', 1024) if vs else 1024
                            h = vs.get('height', 768) if vs else 768
                            tx = _random.randint(80, max(82, w - 80))
                            ty = _random.randint(80, max(82, min(h, 700) - 80))
                            await _mouse_move_bezier(page, tx, ty)
                except Exception:
                    pass

        # try:
        result = None
        if self.use_agent:
            result = await self.use_agent.run(
                max_steps=50, on_step_start=hook, on_step_end=hook
            )
        return result

    async def get_page(self):
        if self.use_agent and self.browser_session:
            try:
                return await self.use_agent.browser_session.get_current_page() if self.use_agent.browser_session else None
            except Exception:
                # Browser session might be closed or invalid
                return None
        return None

    async def get_selector_map(self):
        """Get the selector map for the current page state."""
        if self.use_agent:
            await self.use_agent.browser_session.get_state_summary(cache_clickable_elements_hashes=True) if self.use_agent.browser_session else None
            return await self.use_agent.browser_session.get_selector_map() if self.use_agent.browser_session else None
            await self.use_agent.browser_session.get_state_summary(
                cache_clickable_elements_hashes=True
            )
            return await self.use_agent.browser_session.get_selector_map()
        return {}


class BrowserAgent(Tool):

    async def execute(self, message="", reset="", **kwargs):
        self.guid = self.agent.context.generate_id() # short random id
        reset = str(reset).lower().strip() == "true"
        await self.prepare_state(reset=reset)
        message = get_secrets_manager(self.agent.context).mask_values(message, placeholder="<secret>{key}</secret>") # mask any potential passwords passed from A0 to browser-use to browser-use format
        task = self.state.start_task(message) if self.state else None

        # wait for browser agent to finish and update progress with timeout
        timeout_seconds = 300  # 5 minute timeout
        start_time = time.time()

        fail_counter = 0
        while not task.is_ready() if task else False:
            # Check for timeout to prevent infinite waiting
            if time.time() - start_time > timeout_seconds:
                PrintStyle().warning(
                    self._mask(f"Browser agent task timeout after {timeout_seconds} seconds, forcing completion")
                )
                break

            await self.agent.handle_intervention()
            # Calibrated to real click-interval distribution: p50=732ms, p75=2482ms
            # Using lognormal (mu=6.6, sigma=1.1) which fits the heavy-right-tail shape
            await asyncio.sleep(max(0.4, min(8.0, _random.lognormvariate(6.6, 1.1) / 1000.0)))
            try:
                if task and task.is_ready():  # otherwise get_update hangs
                    break
                try:
                    update = await asyncio.wait_for(self.get_update(), timeout=10)
                    fail_counter = 0  # reset on success
                except asyncio.TimeoutError:
                    fail_counter += 1
                    PrintStyle().warning(
                        self._mask(f"browser_agent.get_update timed out ({fail_counter}/3)")
                    )
                    if fail_counter >= 3:
                        PrintStyle().warning(
                            self._mask("3 consecutive browser_agent.get_update timeouts, breaking loop")
                        )
                        break
                    continue
                update_log = update.get("log", get_use_agent_log(None))
                self.update_progress("\n".join(update_log))
                screenshot = update.get("screenshot", None)
                if screenshot:
                    self.log.update(screenshot=screenshot)
            except Exception as e:
                PrintStyle().error(self._mask(f"Error getting update: {str(e)}"))

        if task and not task.is_ready():
            PrintStyle().warning(self._mask("browser_agent.get_update timed out, killing the task"))
            self.state.kill_task() if self.state else None
            return Response(
                message=self._mask("Browser agent task timed out, not output provided."),
                break_loop=False,
            )

        # final progress update
        if self.state and self.state.use_agent:
            log_final = get_use_agent_log(self.state.use_agent)
            self.update_progress("\n".join(log_final))

        # collect result with error handling
        try:
            result = await task.result() if task else None
        except Exception as e:
            PrintStyle().error(self._mask(f"Error getting browser agent task result: {str(e)}"))
            # Return a timeout response if task.result() fails
            answer_text = self._mask(f"Browser agent task failed to return result: {str(e)}")
            self.log.update(answer=answer_text)
            return Response(message=answer_text, break_loop=False)
        # finally:
        #     # Stop any further browser access after task completion
        #     # self.state.kill_task()
        #     pass

        # Check if task completed successfully
        if result and result.is_done():
            answer = result.final_result()
            try:
                if answer and isinstance(answer, str) and answer.strip():
                    answer_data = DirtyJson.parse_string(answer)
                    answer_text = strings.dict_to_text(answer_data)  # type: ignore
                else:
                    answer_text = (
                        str(answer) if answer else "Task completed successfully"
                    )
            except Exception as e:
                answer_text = (
                    str(answer)
                    if answer
                    else f"Task completed with parse error: {str(e)}"
                )
        else:
            # Task hit max_steps without calling done()
            urls = result.urls() if result else []
            current_url = urls[-1] if urls else "unknown"
            answer_text = (
                f"Task reached step limit without completion. Last page: {current_url}. "
                f"The browser agent may need clearer instructions on when to finish."
            )

        # Mask answer for logs and response
        answer_text = self._mask(answer_text)

        # update the log (without screenshot path here, user can click)
        self.log.update(answer=answer_text)

        # add screenshot to the answer if we have it
        if (
            self.log.kvps
            and "screenshot" in self.log.kvps
            and self.log.kvps["screenshot"]
        ):
            path = self.log.kvps["screenshot"].split("//", 1)[-1].split("&", 1)[0]
            answer_text += f"\n\nScreenshot: {path}"

        # respond (with screenshot path)
        return Response(message=answer_text, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Calling Browser Agent",
            content="",
            kvps=self.args,
        )

    async def get_update(self):
        await self.prepare_state()

        result = {}
        agent = self.agent
        ua = self.state.use_agent if self.state else None
        page = await self.state.get_page() if self.state else None

        if ua and page:
            try:

                async def _get_update():

                    # await agent.wait_if_paused() # no need here

                    # Build short activity log
                    result["log"] = get_use_agent_log(ua)

                    path = files.get_abs_path(
                        persist_chat.get_chat_folder_path(agent.context.id),
                        "browser",
                        "screenshots",
                        f"{self.guid}.png",
                    )
                    files.make_dirs(path)
                    await page.screenshot(path=path, full_page=False, timeout=3000)
                    result["screenshot"] = f"img://{path}&t={str(time.time())}"

                if self.state and self.state.task and not self.state.task.is_ready():
                    await self.state.task.execute_inside(_get_update)

            except Exception:
                pass

        return result

    async def prepare_state(self, reset=False):
        self.state = self.agent.get_data("_browser_agent_state")
        if reset and self.state:
            self.state.kill_task()
        if not self.state or reset:
            self.state = await State.create(self.agent)
        self.agent.set_data("_browser_agent_state", self.state)

    def update_progress(self, text):
        text = self._mask(text)
        short = text.split("\n")[-1]
        if len(short) > 50:
            short = short[:50] + "..."
        progress = f"Browser: {short}"

        self.log.update(progress=text)
        self.agent.context.log.set_progress(progress)

    def _mask(self, text: str) -> str:
        try:
            return get_secrets_manager(self.agent.context).mask_values(text or "")
        except Exception as e:
            return text or ""

    # def __del__(self):
    #     if self.state:
    #         self.state.kill_task()


def get_use_agent_log(use_agent: browser_use.Agent | None):
    result = ["🚦 Starting task"]
    if use_agent:
        action_results = use_agent.history.action_results() or []
        short_log = []
        for item in action_results:
            # final results
            if item.is_done:
                if item.success:
                    short_log.append("✅ Done")
                else:
                    short_log.append(
                        f"❌ Error: {item.error or item.extracted_content or 'Unknown error'}"
                    )

            # progress messages
            else:
                text = item.extracted_content
                if text:
                    first_line = text.split("\n", 1)[0][:200]
                    short_log.append(first_line)
        result.extend(short_log)
    return result
