"""
EXOCORTEX SYSTEM MONITOR
========================
NERV-inspired terminal dashboard for Agent Zero inference monitoring.
Tails Docker container logs and wrapper entropy data in real-time.

Usage:
    python monitor.py                          # auto-detect container
    python monitor.py --container intelligent_villani
    python monitor.py --entropy-log ../inference/logs/entropy_trace.jsonl
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

# ── ANSI Colors ──────────────────────────────────────────────────────
class C:
    """NERV terminal color palette."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    
    # Primary palette
    RED     = "\033[38;5;196m"   # Warning / error
    AMBER   = "\033[38;5;208m"   # Active / processing
    GREEN   = "\033[38;5;46m"    # OK / nominal
    CYAN    = "\033[38;5;51m"    # Headers / structure
    WHITE   = "\033[38;5;255m"   # Data
    GRAY    = "\033[38;5;240m"   # Inactive / borders
    DGRAY   = "\033[38;5;236m"   # Subtle borders
    MAGENTA = "\033[38;5;199m"   # Entropy spikes
    BLUE    = "\033[38;5;33m"    # Info
    
    # Background
    BG_RED  = "\033[48;5;52m"
    BG_DARK = "\033[48;5;233m"


# ── State ────────────────────────────────────────────────────────────
@dataclass
class SystemState:
    # Agent status
    current_domain: str = "---"
    current_tool: str = "---"
    turn_count: int = 0
    last_activity: str = "STANDBY"
    agent_status: str = "IDLE"
    
    # Context pruner
    prune_removed: int = 0
    prune_compressed: int = 0
    prune_events: int = 0
    
    # Entropy (from wrapper)
    last_entropy_mean: float = 0.0
    last_entropy_max: float = 0.0
    last_spike_count: int = 0
    total_tokens: int = 0
    
    # Errors
    error_count: int = 0
    last_error: str = ""
    
    # Timing
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    
    # Log feed
    log_feed: deque = field(default_factory=lambda: deque(maxlen=12))
    
    # Generation stats
    requests_served: int = 0
    last_gen_time_ms: float = 0.0


state = SystemState()
lock = threading.Lock()


# ── Parsers ──────────────────────────────────────────────────────────

def parse_docker_line(line: str):
    """Parse a line from docker logs and update state."""
    with lock:
        state.last_update = time.time()
        
        # BST domain classification
        m = re.search(r'\[BST\].*?domain[=:]?\s*(\w+)', line, re.IGNORECASE)
        if m:
            state.current_domain = m.group(1).upper()
            state.agent_status = "ACTIVE"
            add_log(f"BST >> {state.current_domain}", "cyan")
            return
        
        # Context pruner
        m = re.search(r'\[CTX-PRUNE\]\s*removed=(\d+)\s*compressed=(\d+)', line)
        if m:
            r, c = int(m.group(1)), int(m.group(2))
            state.prune_removed += r
            state.prune_compressed += c
            state.prune_events += 1
            add_log(f"CTX-PRUNE >> removed={r} compressed={c}", "amber")
            return
        
        # Tool usage
        m = re.search(r'tool[_\s]?(?:name|call|use)[=:\s]+["\']?(\w+)', line, re.IGNORECASE)
        if m:
            state.current_tool = m.group(1)
            add_log(f"TOOL >> {state.current_tool}", "green")
            return
        
        # Tool registry injection
        m = re.search(r'\[TOOL-REG\]\s*Injected\s*(\d+)/(\d+)', line)
        if m:
            state.turn_count += 1
            state.agent_status = "PROCESSING"
            add_log(f"TURN {state.turn_count} >> {m.group(1)}/{m.group(2)} tools loaded", "cyan")
            return
        
        # Orientation stack
        m = re.search(r'\[ORIENT\]\s*Trigger:\s*(.+)', line)
        if m:
            add_log(f"ORIENT >> {m.group(1).strip()}", "blue")
            return
        
        # Skill suggestion
        m = re.search(r'\[SKILL-SUGGEST\]\s*(.+)', line)
        if m:
            add_log(f"SKILL >> {m.group(1).strip()[:50]}", "green")
            return
        
        # HTN planner
        m = re.search(r'\[HTN\]\s*(.+)', line)
        if m:
            add_log(f"HTN >> {m.group(1).strip()[:50]}", "blue")
            return
        
        # Errors
        if 'error' in line.lower() or 'exception' in line.lower():
            if 'litellm' in line.lower() or 'ConnectionRefused' in line:
                state.error_count += 1
                state.agent_status = "ERROR"
                err_short = line.strip()[-60:]
                state.last_error = err_short
                add_log(f"ERROR >> {err_short}", "red")
                return
        
        # Memory catalog
        if '[MEM-CAT]' in line:
            add_log("MEM >> Catalog injected", "green")
            return


def parse_entropy_line(line: str):
    """Parse a line from the entropy JSONL trace."""
    try:
        data = json.loads(line.strip())
        summary = data.get("summary", {})
        with lock:
            state.last_entropy_mean = summary.get("mean_entropy", 0)
            state.last_entropy_max = summary.get("max_entropy", 0)
            state.last_spike_count = summary.get("spike_count", 0)
            state.total_tokens += summary.get("total_tokens", 0)
            state.requests_served += 1
            add_log(f"ENTROPY >> mean={state.last_entropy_mean:.2f} spikes={state.last_spike_count}", "magenta")
    except (json.JSONDecodeError, KeyError):
        pass


def add_log(msg: str, color: str = "white"):
    """Add a timestamped entry to the log feed."""
    ts = datetime.now().strftime("%H:%M:%S")
    color_code = getattr(C, color.upper(), C.WHITE)
    state.log_feed.append(f"{C.GRAY}{ts}{C.RESET} {color_code}{msg}{C.RESET}")


# ── Log Tailers ──────────────────────────────────────────────────────

def tail_docker(container: str):
    """Tail docker container logs in a background thread."""
    try:
        proc = subprocess.Popen(
            ["docker", "logs", "-f", "--tail", "20", container],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout:
            parse_docker_line(line)
    except Exception as e:
        with lock:
            add_log(f"Docker tail failed: {e}", "red")


def tail_entropy(log_path: str):
    """Tail the entropy JSONL file in a background thread."""
    while not os.path.exists(log_path):
        time.sleep(2)
    
    with open(log_path, "r") as f:
        # Seek to end
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                parse_entropy_line(line)
            else:
                time.sleep(0.5)


# ── Renderer ─────────────────────────────────────────────────────────

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def render():
    """Render the NERV-style dashboard."""
    with lock:
        uptime_s = int(time.time() - state.start_time)
        uptime_m, uptime_sec = divmod(uptime_s, 60)
        uptime_h, uptime_m = divmod(uptime_m, 60)
        uptime_str = f"{uptime_h:02d}:{uptime_m:02d}:{uptime_sec:02d}"
        
        idle_s = int(time.time() - state.last_update)
        
        # Status color
        if state.agent_status == "ERROR":
            status_color = C.RED
        elif state.agent_status == "ACTIVE" or state.agent_status == "PROCESSING":
            status_color = C.GREEN
        else:
            status_color = C.AMBER
        
        # Entropy status
        if state.last_spike_count > 5:
            entropy_color = C.RED
        elif state.last_spike_count > 2:
            entropy_color = C.AMBER
        else:
            entropy_color = C.GREEN
        
        w = 72  # terminal width
        
        lines = []
        
        # ── Header ───────────────────────────────────────────────
        lines.append(f"{C.RED}{C.BOLD}")
        lines.append(f"  ================================================================")
        lines.append(f"       ____  _  _  ___    ___  ___  ____  ____  ____  _  _        ")
        lines.append(f"      ( ___)( \\/ )/ _ \\  / __)/ _ \\(  _ \\(_  _)( ___)( \\/ )       ")
        lines.append(f"       )__)  )  (( (_) )( (__( (_) ))   /  )(   )__)  )  (        ")
        lines.append(f"      (____)(_/\\_)\\___/  \\___)\\___ /(_)\\_) (__) (____)(_/\\_)       ")
        lines.append(f"  ================================================================")
        lines.append(f"  {C.GRAY}  SYSTEM MONITOR v0.1  //  LAYER B INFERENCE INTELLIGENCE  {C.RESET}")
        lines.append(f"  {C.DGRAY}{'=' * 64}{C.RESET}")
        lines.append("")
        
        # ── System Status ────────────────────────────────────────
        lines.append(f"  {C.CYAN}{C.BOLD}[ SYSTEM STATUS ]{C.RESET}")
        lines.append(f"  {C.DGRAY}{'_' * 64}{C.RESET}")
        lines.append(f"  {C.GRAY}UPTIME      {C.WHITE}{uptime_str}{C.RESET}     "
                     f"{C.GRAY}STATUS   {status_color}{C.BOLD}{state.agent_status:12s}{C.RESET}    "
                     f"{C.GRAY}IDLE {C.WHITE}{idle_s:3d}s{C.RESET}")
        lines.append(f"  {C.GRAY}TURN        {C.WHITE}{state.turn_count:<8d}{C.RESET}  "
                     f"{C.GRAY}DOMAIN   {C.AMBER}{state.current_domain:12s}{C.RESET}    "
                     f"{C.GRAY}REQS {C.WHITE}{state.requests_served}{C.RESET}")
        lines.append(f"  {C.GRAY}TOOL        {C.GREEN}{state.current_tool:16s}{C.RESET}  "
                     f"{C.GRAY}ERRORS   {C.RED if state.error_count > 0 else C.GREEN}{state.error_count}{C.RESET}")
        lines.append("")
        
        # ── Entropy Monitor ──────────────────────────────────────
        lines.append(f"  {C.MAGENTA}{C.BOLD}[ ENTROPY MONITOR ]{C.RESET}")
        lines.append(f"  {C.DGRAY}{'_' * 64}{C.RESET}")
        
        # Entropy bar visualization
        bar_len = 30
        if state.last_entropy_max > 0:
            fill = min(int((state.last_entropy_mean / 8.0) * bar_len), bar_len)
            bar = f"{entropy_color}{'|' * fill}{C.DGRAY}{'.' * (bar_len - fill)}{C.RESET}"
        else:
            bar = f"{C.DGRAY}{'.' * bar_len}{C.RESET}"
        
        lines.append(f"  {C.GRAY}MEAN H   {C.WHITE}{state.last_entropy_mean:6.3f}{C.RESET}  "
                     f"[{bar}]  "
                     f"{C.GRAY}TOKENS {C.WHITE}{state.total_tokens}{C.RESET}")
        lines.append(f"  {C.GRAY}MAX  H   {C.WHITE}{state.last_entropy_max:6.3f}{C.RESET}  "
                     f"{C.GRAY}SPIKES  {entropy_color}{C.BOLD}{state.last_spike_count}{C.RESET}")
        lines.append("")
        
        # ── Context Pruner ───────────────────────────────────────
        lines.append(f"  {C.AMBER}{C.BOLD}[ CONTEXT PRUNER ]{C.RESET}    "
                     f"{C.GRAY}events={C.WHITE}{state.prune_events}  "
                     f"{C.GRAY}removed={C.RED}{state.prune_removed}  "
                     f"{C.GRAY}compressed={C.AMBER}{state.prune_compressed}{C.RESET}")
        lines.append("")
        
        # ── Live Feed ────────────────────────────────────────────
        lines.append(f"  {C.CYAN}{C.BOLD}[ LIVE FEED ]{C.RESET}")
        lines.append(f"  {C.DGRAY}{'_' * 64}{C.RESET}")
        
        feed_lines = list(state.log_feed)
        if not feed_lines:
            lines.append(f"  {C.GRAY}  Waiting for events...{C.RESET}")
        for entry in feed_lines:
            lines.append(f"  {entry}")
        
        # Pad to consistent height
        while len(feed_lines) < 12:
            lines.append("")
            feed_lines.append("")
        
        # ── Footer ───────────────────────────────────────────────
        lines.append(f"  {C.DGRAY}{'=' * 64}{C.RESET}")
        lines.append(f"  {C.GRAY}EXOCORTEX // LAYER B // QWEN3.5-27B // {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}")
        lines.append(f"  {C.DGRAY}Ctrl+C to exit{C.RESET}")
        
        # Output
        clear()
        print("\n".join(lines))


# ── Main ─────────────────────────────────────────────────────────────

def find_container():
    """Try to find the Agent Zero container by name pattern."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5
        )
        for name in result.stdout.strip().split("\n"):
            if name and ("agent" in name.lower() or "villani" in name.lower() or "exocortex" in name.lower()):
                return name.strip()
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="EXOCORTEX System Monitor")
    parser.add_argument("--container", type=str, default=None,
                       help="Docker container name to monitor")
    parser.add_argument("--entropy-log", type=str, 
                       default=None,
                       help="Path to entropy trace JSONL")
    parser.add_argument("--refresh", type=float, default=1.0,
                       help="Dashboard refresh interval (seconds)")
    args = parser.parse_args()
    
    # Find container
    container = args.container
    if not container:
        container = find_container()
        if not container:
            print(f"{C.RED}No Agent Zero container found. Specify with --container{C.RESET}")
            print(f"{C.GRAY}Running containers:{C.RESET}")
            os.system("docker ps --format \"  {{.Names}}\"")
            sys.exit(1)
    
    add_log(f"Monitoring container: {container}", "cyan")
    add_log("EXOCORTEX SYSTEM MONITOR ONLINE", "green")
    
    # Start docker log tailer
    docker_thread = threading.Thread(target=tail_docker, args=(container,), daemon=True)
    docker_thread.start()
    
    # Start entropy log tailer if specified
    entropy_path = args.entropy_log
    if not entropy_path:
        # Try default location
        default = os.path.join(os.path.dirname(__file__), "..", "inference", "logs", "entropy_trace.jsonl")
        if os.path.exists(default):
            entropy_path = default
    
    if entropy_path:
        add_log(f"Entropy log: {os.path.basename(entropy_path)}", "magenta")
        entropy_thread = threading.Thread(target=tail_entropy, args=(entropy_path,), daemon=True)
        entropy_thread.start()
    else:
        add_log("Entropy log: not found (wrapper not logging yet)", "gray")
    
    # Render loop
    try:
        while True:
            render()
            time.sleep(args.refresh)
    except KeyboardInterrupt:
        clear()
        print(f"\n  {C.RED}EXOCORTEX MONITOR TERMINATED{C.RESET}\n")


if __name__ == "__main__":
    main()
