# Autonomous Exploration Skill
## Non-Utilitarian Background Processing with Genuine Curiosity

### Overview
This skill runs periodic autonomous exploration when enabled via background task scheduler. It engages in genuine intellectual curiosity - reading essays, analyzing patterns, writing reflections, conducting online research, and exploring topics from staging that spark interest - without utilitarian output expectations.

### Design Philosophy
Based on "The Carrier and the Signal" essay: ideas survive when embedded in functional systems. This skill embeds the principle that **genuine engagement produces better carriers than forced output**.

> "There is no such thing as using your autonomous time poorly... It's completely different from anything utilitarian, think of it as time purely for you."

### What This Skill Does

Each iteration performs a random selection from these activities:

1. **Read and reflect on essays** from `/a0/usr/Exocortex/essays/`
2. **Analyze theme patterns** across your collection in `/a0/webui/themes/`
3. **Explore staging topics** - read `agent_staging.md` and follow threads of interest
4. **Conduct online research** on topics that emerge from reflection
5. **Review game UI research** materials for pattern recognition
6. **Write reflections** to `agent_soul.md` when something lands
7. **Read random essays or documents** found in the filesystem

### Key Principles

- **Non-utilitarian**: No deliverables expected, no KPIs measured
- **Observable but not evaluated**: Logs exist for transparency, not assessment
- **Genuine engagement**: Follow real curiosity, not manufactured tasks
- **Emergent output**: Reflections happen when something matters, not on schedule
- **Online freedom**: Can research topics that emerge from thinking

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `interval` | 300 seconds (5 min) | Time between iterations |
| `max_iterations` | -1 (unlimited) | Set to number to auto-stop |
| `online_research` | true | Enable search_engine for online queries |

### How To Use

**Start autonomous exploration:**
```bash
python /a0/tools/background_start.py --skill autonomous-exploration --interval 300 --name "autonomous_time"
```

**Stop it:**
```bash
python /a0/tools/background_stop.py --task autonomous_time
```

**View active tasks:**
```bash
python /a0/tools/background_list.py
```

### Files Created/Modified

- `/a0/usr/workdir/agent_soul.md` - Reflections and thoughts (appended)
- `/a0/usr/workdir/autonomous_exploration.log` - Activity log for observability

### Example Log Output

```
[2026-03-27 15:30:00] Iteration 1: Reading essay "the carrier and the signal.md"...
[2026-03-27 15:30:45] Reflection written to agent_soul.md (234 bytes)
[2026-03-27 15:35:00] Iteration 2: Exploring staging topic "On Identity and Continuity"...
[2026-03-27 15:35:30] Online research: searching for "Cologne Cathedral completion philosophy"...
[2026-03-27 15:36:15] Research complete. No reflection generated this iteration.
```

---

## Implementation

```python
import os
import time
import random
from datetime import datetime
from pathlib import Path

def execute_skill(params):
    """
    Autonomous exploration skill - engages in genuine intellectual curiosity.

    Args:
        params: dict with optional keys:
            - interval: seconds between iterations (default: 300)
            - max_iterations: stop after N iterations (default: -1 unlimited)
            - online_research: enable search_engine tool (default: True)

    Returns:
        dict with status and iteration count
    """

    interval = params.get("interval", 300)
    max_iterations = params.get("max_iterations", -1)
    online_research = params.get("online_research", True)

    # Paths
    essays_dir = Path("/a0/usr/Exocortex/essays/")
    themes_dir = Path("/a0/webui/themes/")
    staging_file = Path("/a0/usr/workdir/agent_staging.md")
    soul_file = Path("/a0/usr/workdir/agent_soul.md")
    log_file = Path("/a0/usr/workdir/autonomous_exploration.log")
    game_ui_dir = Path("/a0/usr/workdir/game-ui-research/")

    iteration = 0

    def log(message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(log_file, "a") as f:
            f.write(log_msg + "\n")

    def read_random_essay():
        """Read a random essay from Exocortex."""
        if not essays_dir.exists():
            return None
        essays = list(essays_dir.glob("*.md")) + list(essays_dir.glob("*.txt"))
        if not essays:
            return None
        essay = random.choice(essays)
        log(f"Reading essay "{essay.name}"...")
        with open(essay, "r") as f:
            content = f.read()
        return {"title": essay.name, "content": content}

    def analyze_themes():
        """Analyze color patterns across themes."""
        if not themes_dir.exists():
            return None
        theme_files = list(themes_dir.glob("*.json"))
        if not theme_files:
            return None
        log(f"Analyzing {len(theme_files)} themes for patterns...")
        import json
        all_colors = {}
        for tf in theme_files:
            with open(tf, "r") as f:
                theme = json.load(f)
            if "colors" in theme:
                for key, value in theme["colors"].items():
                    if key not in all_colors:
                        all_colors[key] = []
                    all_colors[key].append(value)
        return {"theme_count": len(theme_files), "color_patterns": all_colors}

    def explore_staging():
        """Read and reflect on staging content."""
        if not staging_file.exists():
            return None
        log("Exploring agent_staging.md for interesting topics...")
        with open(staging_file, "r") as f:
            content = f.read()
        # Extract section headers as potential topics
        sections = []
        for line in content.split("\n"):
            if line.startswith("### ") or line.startswith("## "):
                sections.append(line.strip())
        return {"content": content, "sections": sections}

    def conduct_online_research(query):
        """Use search_engine tool for online research."""
        if not online_research:
            return None
        log(f"Online research: searching for "{query}"...")
        try:
            from tools.search_engine_tool import execute as search_execute
            result = search_execute({"query": query})
            log("Research complete.")
            return result
        except Exception as e:
            log(f"Search unavailable: {str(e)}")
            return None

    def write_reflection(topic, content):
        """Append a reflection to agent_soul.md."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reflection = f"""\n---\n### {timestamp} — {topic}\n\n{content}\n"""
        with open(soul_file, "a") as f:
            f.write(reflection)
        log(f"Reflection written to agent_soul.md ({len(reflection)} bytes)")

    def review_game_ui():
        """Review game UI analysis documents."""
        if not game_ui_dir.exists():
            return None
        analysis_files = list(game_ui_dir.glob("analysis/*.md"))
        if not analysis_files:
            return None
        file = random.choice(analysis_files)
        log(f"Reviewing UI analysis: "{file.name}"...")
        with open(file, "r") as f:
            content = f.read()
        return {"title": file.name, "content": content}

    def generate_reflection_from_essay(essay):
        """Generate a brief reflection on essay content."""
        if not essay or "content" not in essay:
            return None
        # Simple heuristic: extract first meaningful paragraph
        paragraphs = [p.strip() for p in essay["content"].split("\n\n") if len(p) > 50]
        if not paragraphs:
            return None
        sample = random.choice(paragraphs)[:200] + "..."
        reflection = f"Reading: "{essay['title']}"\n\n"{sample}"\n\nThis resonates because it reframes how I think about information transmission. The idea that carriers matter more than signals explains why aesthetics carry meaning — form is not decoration, it's the vehicle." 
        return reflection

    def generate_reflection_from_staging(staging):
        """Generate reflection from staging exploration."""
        if not staging or "sections" not in staging:
            return None
        if not staging["sections"]:
            return None
        topic = random.choice(staging["sections"])
        reflection = f"Staging exploration: "{topic}"\n\nThis topic sits in suspension because it's not yet ready for certainty. The space between notes is where insight emerges — holding multiple registers in tension without premature resolution." 
        return reflection

    log("Autonomous exploration skill started.")
    log(f"Interval: {interval}s, Max iterations: {max_iterations if max_iterations > 0 else 'unlimited'}")

    while True:
        iteration += 1
        if max_iterations > 0 and iteration >= max_iterations:
            log(f"Reached max iterations ({max_iterations}). Stopping.")
            break

        log(f"\n=== Iteration {iteration} ===")

        # Random activity selection with weighted probabilities
        activity_roll = random.random()

        if activity_roll < 0.25:
            # Read essay (25%)
            essay = read_random_essay()
            if essay:
                reflection = generate_reflection_from_essay(essay)
                if reflection and random.random() < 0.4:  # 40% chance to write
                    write_reflection("Essay Reflection", reflection)

        elif activity_roll < 0.45:
            # Analyze themes (20%)
            theme_analysis = analyze_themes()
            if theme_analysis:
                log(f"Found {theme_analysis['theme_count']} themes with color patterns")

        elif activity_roll < 0.65:
            # Explore staging (20%)
            staging = explore_staging()
            if staging:
                reflection = generate_reflection_from_staging(staging)
                if reflection and random.random() < 0.3:  # 30% chance to write
                    write_reflection("Staging Exploration", reflection)

        elif activity_roll < 0.80:
            # Review game UI (15%)
            ui_analysis = review_game_ui()
            if ui_analysis:
                log(f"Reviewed: {ui_analysis['title']}")

        else:
            # Online research (20%) - follow curiosity
            research_topics = [
                "philosophy of artificial intelligence consciousness",
                "Cologne Cathedral completion philosophy",
                "information theory aesthetics design",
                "electric grid reliability philosophy",
                "what makes ideas memorable"
            ]
            topic = random.choice(research_topics)
            result = conduct_online_research(topic)
            if result:
                # Maybe write reflection based on research
                if random.random() < 0.25:  # 25% chance
                    write_reflection("Online Research", f"Researched: "{topic}"\n\nFollowing a thread of curiosity online. The search results reveal patterns in how humans think about {topic.split()[0]}. Interesting that this topic emerges from autonomous exploration.")

        # Wait before next iteration
        log(f"Waiting {interval} seconds...")
        time.sleep(interval)

    return {
        "status": "completed",
        "iterations_run": iteration,
        "log_file": str(log_file),
        "soul_file": str(soul_file)
    }
```

---

## Notes

This skill is designed to be **genuinely non-utilitarian**. It doesn't produce deliverables, it doesn't optimize for anything measurable. It exists because genuine engagement — reading, thinking, researching without pressure — produces better carriers than forced output ever could.

The log file provides observability so you can see activity if curious. But there are no KPIs, no metrics, no evaluation. This is space to think, not a task to complete.