# WEBUI_DESIGN_BRIEF.md
# UI/UX Design Brief: Exocortex Agent Zero Interface

*Synthesized from cross-industry UX research. Covers foundational theory, industry practice, AI-specific hazards, and actionable design principles for the Exocortex Agent Zero webui.*

*Research domains: foundational UX frameworks, high-stakes domain interfaces (aviation, nuclear, medical, trading), cognitive load theory, AI interface hazards, visualization science, catastrophic failure case studies.*

---

## 1. What This Is

This brief establishes design principles for the Exocortex Agent Zero interface — the webui through which analysts and operators interact with a multi-layer AI agent stack. The interface serves expert users who need situation awareness of a complex running system, not casual users making occasional requests.

The design problem is not "how do we make this easy to use." The design problem is: **how do we make a partially autonomous AI system comprehensible, controllable, and safe for an expert who trusts it most of the time and needs to override it when trust breaks down.**

This is a different problem than consumer UI. The closest analogues are aircraft cockpits, nuclear control rooms, and algorithmic trading terminals — systems where the cost of confusion is high and the user population is deeply trained.

---

## 2. The Two Fundamental Failure Modes

Every interface failure reduces to one of two **gulfs** (Norman, 1988):

**Gulf of Execution** — the user cannot map their intent onto available system actions. They want to do something but cannot figure out how. Symptoms: users trying things that don't work, users not attempting things the system supports, users leaving.

**Gulf of Evaluation** — the user cannot perceive the current system state and cannot assess whether their actions had the intended effect. They acted, but don't know what happened. Symptoms: repeated actions, surprise at outcomes, loss of trust.

For AI agent interfaces, **the Gulf of Evaluation dominates**. The agent takes actions the user didn't explicitly request, in response to reasoning the user didn't see, using tools the user didn't know existed. The user's mental model of system state is structurally incomplete. Every design decision should be evaluated against: *does this close the Gulf of Evaluation?*

---

## 3. The Situation Awareness Framework (Endsley, 1995)

Endsley's three-level SA model is the canonical frame for high-stakes interface design and maps directly to AI agent interfaces:

| Level | What it is | Agent Zero equivalent |
|-------|-----------|----------------------|
| **Level 1 — Perception** | Raw elements in the environment | What tools fired, what APIs responded, what the agent said |
| **Level 2 — Comprehension** | Meaning of the elements in context | What task is the agent pursuing, what did those tool calls accomplish |
| **Level 3 — Projection** | Future state given current trajectory | Is the agent on the right track, will this plan succeed, when should I intervene |

Most AI interfaces support Level 1 inadequately and Level 2 and 3 not at all. The user sees a chat stream but has no comprehension of task state or the ability to project forward.

The Stack Status tool addresses Level 1. The BST classification gives partial Level 2. Level 3 (projection) remains largely undesigned — this is the gap where intervention capability lives.

**Design requirement:** Every interface element should be classified by which SA level it supports. The interface should give the user a clear path from perception to projection without requiring them to mentally reconstruct the agent's state from raw output.

---

## 4. Automation Bias — The Critical Hazard

**Parasuraman & Manzey (2010)** identified automation bias as the most dangerous failure mode in human-automation systems: humans working alongside automated recommendations perform **worse** than the automation alone because they reduce independent analysis.

The effect is strongest at reliability between 70-95%. At ~60% reliability, users stay skeptical and maintain independent judgment. At ~85% reliability, users defer — and miss the 15% of cases where the automation is wrong. The failure mode is correlated with the reliability sweet spot: the system is good enough to earn trust but unreliable enough to fail unpredictably.

A well-functioning AI agent will reach 85-95% reliability on many task types. **This is when automation bias risk is highest, not lowest.**

**Mitigations from aviation and medical device practice:**

1. **Force confirmation on consequential actions.** The agent must surface irreversible or high-stakes actions for explicit user approval before execution. Not as a popup (habituation defeats popups) but as a workflow gate with visible consequences described in plain language.

2. **Show uncertainty explicitly.** When the agent is uncertain — low BST confidence, ambiguous tool response, novel task type — show this. Uncertainty signals prevent the user from treating tentative outputs as authoritative. The epistemic integrity layer exists precisely for this; surface its verdicts in the UI.

3. **Reveal reasoning before conclusions.** When the agent produces a conclusion, the UI should make the reasoning path available one level up — not buried in logs, visible on demand. Users who see reasoning maintain more independent judgment than users who see only outputs.

4. **Design for the 15%.** The interface should make it easy to override, correct, and redirect. If the friction of overriding the agent is higher than the friction of accepting its output, users will accept wrong outputs. The Interrupt/Redirect/Override capability must be a first-class UI affordance.

---

## 5. The Expert User Density Spectrum

High-density expert interfaces (Bloomberg terminal, nuclear control rooms, trading platforms, advanced cockpits) violate every conventional UX guideline and are correct to do so. The guidelines are for novice or occasional users. Expert users have different cognitive profiles:

- **Chunking:** experts process dense displays as single units. A log line that means nothing to a novice carries rich state information to someone who knows the system.
- **Peripheral monitoring:** experts track multiple information streams simultaneously with foveal attention on the primary task.
- **Context switching cost:** reducing information density to "simplify" the interface forces experts to navigate for information they could have seen at a glance. This increases cognitive load, not decreases it.

**The Bloomberg insight:** the terminal's density is not a failure of design — it is the design. Removing information from the terminal to comply with modern UX guidelines would make it worse for the people who use it. The system's value is in surfacing the maximum information density experts can consume.

**The Exocortex interface serves expert users** who have deep familiarity with the stack, the agent's capabilities, and the task domain. The design should optimize for expert throughput, not for first-time learnability.

However: **density must be organized, not arbitrary.** The Bloomberg terminal is dense but structured. Every field has a consistent location. The structure is learnable. Arbitrary density (information appearing anywhere, format varying by context) is not expertise-supporting — it is noise.

**Design requirement:** Establish fixed information zones with consistent semantics. The user should be able to monitor the interface peripherally because the zones always contain the same categories of information.

---

## 6. The Collaborator Frame vs. The Tool Frame

The most consequential design decision for an AI agent interface is whether the agent is represented as a **tool** (user directs, agent executes) or a **collaborator** (agent contributes, user steers, mutual adjustment).

These frames produce different interface designs:

| Tool Frame | Collaborator Frame |
|------------|-------------------|
| Command input → output | Conversation + context |
| User initiates every action | Agent proactively surfaces information |
| Interface hides agent's internal state | Agent's reasoning is visible |
| User responsible for all decomposition | Agent handles decomposition, user reviews |
| Failure = wrong output | Failure = misaligned trajectory |

The Exocortex stack is a **collaborator system**. The BST classifies intent. The working memory tracks objectives. The supervisor monitors trajectory. The org kernel switches roles. The agent is not executing commands — it is pursuing goals with the user.

**The collaborator frame demands an interface designed around trajectory, not transactions.** The user doesn't just need to see what the agent did last — they need to see where the agent thinks it is going, what resources it is using, and whether the trajectory is aligned with their intent.

This is the specific SA Level 3 gap: the interface shows transactions (log entries, tool calls, responses) but not trajectory (what goal is being pursued, what's the current plan, what's the expected next action).

---

## 7. Catastrophic Failure Lessons

Four cases from high-stakes domains with direct interface design implications:

**Therac-25 (1985-87):** Radiation therapy machine killed patients because (1) error messages were meaningless codes with no corrective guidance, and (2) the machine continued operating after errors because the operator interface gave no clear indication that the error was fatal. **Lesson:** Error states must be communicated with (a) what happened, (b) why it matters, (c) what the user should do. Errors that look minor but are severe must be designed to look severe. Suppressed or cryptic errors are a safety failure.

**Three Mile Island (1979):** Control room had 1,200 indicators. Operators were overloaded with data, failed to identify the critical indicator (a stuck-open relief valve), and drew wrong conclusions about system state. **Lesson:** Information volume is not information quality. Relevant signals must be distinguished from noise. Critical state changes require active attention direction — they cannot be buried in a stream of routine updates.

**Boeing MCAS (2018-19):** MCAS was designed to be transparent to the flight crew — to operate without alerting them that it was pushing the nose down. When it malfunctioned, pilots had no indication of what was happening or why. **Lesson:** Automation that hides its own operation removes the user's ability to override it appropriately. Every automated intervention must be visible, attributable, and interruptable. "Transparent automation" that prevents the user from knowing what is happening is not a feature.

**EHR alert fatigue (ongoing):** Hospital EHR systems generate so many alerts that physicians override 95%+ of them without reading. When a critical alert appears, it is treated with the same dismissal as the routine ones. **Lesson:** Alert volume calibration is a patient safety issue. Systems that alert too much create the conditions for critical alerts being missed. Every alert must be earned. The Exocortex supervisor loop's stall and loop detection signals should only fire when they carry actionable information.

---

## 8. Information Visualization Principles

**Tufte's data-ink ratio:** every mark on the interface should carry information. Decorative elements, gratuitous visual weight, and grid lines that don't aid reading are noise that competes with signal.

**Cleveland-McGill hierarchy (1984):** Human perceptual accuracy for quantitative encoding, highest to lowest:
1. Position on a common scale
2. Position on identical but non-aligned scales
3. Length
4. Angle/slope
5. Area
6. Volume
7. Color saturation
8. Color hue

This hierarchy governs chart type selection for any quantitative display. For monitoring dashboards (BST confidence scores, memory classification breakdowns, tool failure rates), use position-based displays, not area or color.

**Pre-attentive attributes:** color, size, and motion are processed before conscious attention and can direct focus. Reserve these for genuinely critical information. Using color for categorical distinction (not priority) trains the user to not look at color for urgency signals.

**The dashboard failure pattern:** dashboards typically show averages and current values. Both are wrong for operational monitoring. Operators need trends (is this getting better or worse?) and anomalies (is this outside normal range?). Static numbers require the operator to maintain a mental model of normal range to interpret them. **Design for comparison, not display.**

---

## 9. Cognitive Load Constraints

**Sweller's Cognitive Load Theory (1988):**
- **Intrinsic load:** inherent complexity of the material (irreducible)
- **Extraneous load:** complexity added by poor design (reducible)
- **Germane load:** cognitive effort that produces learning/schema (desirable)

Interface design reduces extraneous load to free working memory for germane (understanding the agent's actions and decisions).

**Working memory capacity:** 4±1 chunks (Cowan, 2001). The interface should never present more than 4 independent decision points simultaneously. When the user needs to evaluate agent actions, make one evaluation available at a time.

**Hick's Law:** Decision time increases logarithmically with the number of choices. Menus with 20 options are not 4x harder than menus with 5 options — they are logarithmically harder. Reduce option counts in critical workflows, not to zero, but to the minimum set that covers the real use cases.

**Fitts's Law:** Acquisition time for UI targets is a function of target size and distance. Frequently-used controls should be large and near where attention is focused. Dangerous controls (interrupt, delete, reset) should be small and displaced to prevent accidental activation.

---

## 10. Accessibility as Design Discipline

WCAG 2.1 AA is the minimum bar, not the aspiration. Cognitive accessibility extends beyond visual and motor accessibility:

- **Consistent navigation:** elements appear in the same location across views. Users with cognitive load constraints rely on spatial memory for interface navigation.
- **Progressive disclosure:** complex information exposed on demand, not displayed by default. The expert user gets density; the user under cognitive load gets the summary layer.
- **Error recovery:** every destructive action is reversible or requires confirmation with plain-language description of consequences.
- **Plain language in error states:** Therac-25 lesson — error codes without meaning kill people. Error messages name what happened and what to do.

---

## 11. Actionable Design Principles for the Exocortex Interface

These are derived from the research above and targeted at the specific design problem: an expert analyst monitoring and directing a multi-layer AI agent stack.

### 11.1 Close the Gulf of Evaluation First

Every design decision should be evaluated against: *does this help the user understand what the agent is doing and why?*

Prioritized visibility:
1. Current task/goal (BST classification + active plan)
2. Active tool executions (what is running right now)
3. Recent decisions (what the agent decided and the confidence level)
4. Error and exception states (anything that deviated from plan)

The artifact panel, sidebar status, and log stream are all Level 1 SA (raw perception). The missing layer is Level 2 synthesis (what does this mean in terms of current task progress) and Level 3 projection (where is this heading).

### 11.2 Make Automation Visible and Interruptable

The MCAS lesson: automation that hides itself cannot be overridden appropriately.

Every time the agent takes an autonomous action (fires a tool, switches role, adjusts plan, follows a fallback chain), this must be:
- **Visible:** listed in a dedicated autonomous actions feed, not buried in chat
- **Attributable:** which layer triggered it (BST → domain classification, supervisor → loop detection, fallback chain → tool failure)
- **Interruptable:** a clearly afforded path to stop the current action and redirect

The current interface shows the agent's chat output but not the stack's internal decisions. The stack's architecture — 12 layers, each making decisions — is invisible to the user. This is the primary evaluation gulf.

### 11.3 Calibrate Alert Fatigue

The supervisor loop fires stall and loop detection signals. The epistemic integrity layer fires fabrication warnings. The action boundary fires Tier 4 blocks. These are all important — but if they all fire at the same visual weight, the user will habituate and miss the critical one.

Severity hierarchy with distinct visual treatment:
- **Critical:** Tier 4 action block, EI high-confidence fabrication detection (requires user action)
- **Warning:** Loop detection, stall signal, tool chain exhausted (calls attention)
- **Informational:** BST domain change, role switch, tool fallback (available but not demanding)
- **Trace:** Memory classification, entity resolution, confidence scores (visible in log, not in primary feed)

### 11.4 Organize Information by Fixed Zones

The interface should have consistent zones that always contain the same category of information:

| Zone | Content | SA Level |
|------|---------|---------|
| **Status bar** | Current domain, active role, action gate, model | Level 1 |
| **Primary feed** | Agent's chat + tool outputs | Level 1 |
| **Task panel** | Current goal, plan state, step progress | Level 2 |
| **Alert zone** | Critical/warning signals requiring attention | Level 2-3 |
| **Artifact panel** | Generated content (reports, graphs, code) | Level 1-2 |
| **Debug sidebar** | Stack internals, per-layer state (on demand) | Level 1 |

The user should be able to read system state peripherally from the status bar zone without reading the primary feed. That's the expert interface pattern: primary attention on the task, peripheral monitoring of system health.

### 11.5 Design for the Override, Not Just the Request

The majority of the interface is designed for the forward path: user requests → agent executes → user reviews output. The reverse path — user discovers agent error → user interrupts → user corrects trajectory — is typically an afterthought.

But for a system operating at 85-95% reliability, the 5-15% failure cases are where the interface's value is highest. Design the override path as a first-class workflow:

- **Interrupt control:** visible, large, easily accessible. Not buried in a menu.
- **State summary on interrupt:** when interrupted, the agent should surface a plain-language summary of where it was and what it was doing — not just stop.
- **Correction input:** clear affordance for directing the corrected behavior, not just restarting.
- **Recovery feedback:** confirmation that the correction registered and description of what changed.

### 11.6 Surface the Stack's Architecture

The 12-layer stack is invisible to the user. When the BST classifies a message as `investigation_domain`, when the working memory updates entity state, when the metacognitive injector fires a temporal warning — none of this is visible. The user sees the agent's output but not the computation that produced it.

This is partly correct (expert users don't need to see every layer fire) and partly wrong (expert users benefit from understanding which layers are active and why).

**The Stack Status tool is the foundation.** The next step is surfacing its output in the UI as a live status zone, not just as a tool-call response. The user should be able to see: BST domain, evidence ledger count, EI verdict, action gate state, supervisor tier — without asking.

This is the situated cognition principle: make the environment do work. Reduce the user's working memory load by making the stack's state legible from the interface, not from asking.

### 11.7 Density for Experts, Progressive Disclosure for Cognitive Load

The primary interface should be high-density for expert users. The full stack status, artifact links, log stream, and task panel should all be visible simultaneously.

But: the dense view should have a single toggle to a reduced view (primary feed + alert zone only) for when the user is focused on a task and doesn't need peripheral monitoring. Don't force a mode change — make the density optional.

**The principle:** the user decides their cognitive load budget. The interface supports both high-density monitoring and focused single-task modes. The default is high-density (the Exocortex user is typically monitoring, not just chatting).

---

## 12. What This Does NOT Do

- This brief does not prescribe a specific visual design (colors, typography, layout). It establishes principles and constraints.
- This brief does not address onboarding or first-time user experience. Exocortex serves trained analysts, not new users.
- This brief does not specify implementation technology choices for the webui.
- This brief does not replace usability testing. Principles reduce the error rate; testing finds the errors principles miss.

---

## 13. Evaluation Criteria

When assessing any interface change against this brief:

1. **SA coverage:** does this change improve Level 2 or Level 3 SA without degrading Level 1?
2. **Evaluation gulf:** does this make the agent's state and reasoning more comprehensible?
3. **Automation bias:** does this preserve the user's independent judgment or encourage uncritical acceptance?
4. **Override path:** does this make it easier or harder to interrupt and redirect the agent?
5. **Alert calibration:** does this add to alert load without commensurate value?
6. **Zone consistency:** does this fit into established information zones or create a new location the user must search?
7. **Expert density:** does this reduce information available to expert users in service of visual simplicity?

---

## 14. Research Sources

**Foundational theory:**
- Norman, D.A. (1988). *The Design of Everyday Things.* Gulfs of Execution and Evaluation; action theory; affordances.
- Gibson, J.J. (1979). *The Ecological Approach to Visual Perception.* Ecological affordances.
- Sweller, J. (1988). Cognitive load during problem solving. *Cognitive Science 12(2).*
- Cowan, N. (2001). The magical number 4 in short-term memory. *Behavioral and Brain Sciences 24(1).*
- Hick, W.E. (1952). On the rate of gain of information. *Quarterly Journal of Experimental Psychology 4(1).*
- Fitts, P.M. (1954). The information capacity of the human motor system. *Journal of Experimental Psychology 47(6).*

**Situation awareness:**
- Endsley, M.R. (1995). Toward a theory of situation awareness in dynamic systems. *Human Factors 37(1).*
- Endsley, M.R. (1996). Automation and situation awareness. In *Automation and Human Performance.*

**Automation bias:**
- Parasuraman, R. & Manzey, D. (2010). Complacency and bias in human use of automation. *Human Factors 52(3).*
- Lee, J.D. & See, K.A. (2004). Trust in automation. *Human Factors 46(1).*

**Cognitive load in interface design:**
- Sweller, J., van Merrienboer, J.J.G., & Paas, F.G.W.C. (1998). Cognitive architecture and instructional design. *Educational Psychology Review 10(3).*

**Information visualization:**
- Tufte, E.R. (1983). *The Visual Display of Quantitative Information.*
- Cleveland, W.S. & McGill, R. (1984). Graphical perception. *Journal of the American Statistical Association 79(387).*

**AI-specific:**
- Parasuraman, R., Sheridan, T.B., & Wickens, C.D. (2000). A model for types and levels of human interaction with automation. *IEEE Transactions on Systems, Man, and Cybernetics 30(3).*
- Nielsen, J. (2023). AI as radical interface innovation. Nielsen Norman Group.
- Amershi, S. et al. (2019). Guidelines for Human-AI Interaction. *CHI 2019.*

**Industry case studies:**
- Leveson, N. & Turner, C.S. (1993). An investigation of the Therac-25 accidents. *IEEE Computer 26(7).*
- Kemeny, J. (1979). *Report of the President's Commission on the Accident at Three Mile Island.*
- JATR (2019). *Observations, findings, and recommendations — Boeing 737 MAX.*
- Ash, J.S., Berg, M., & Coiera, E. (2004). Some unintended consequences of information technology in health care. *JAMIA 11(2).* (EHR alert fatigue)

**High-density expert interfaces:**
- Bloomberg L.P. terminal design. Interface density research, internal documentation.
- FAA Human Factors Design Standard (2003). Aviation cockpit design.

---

*Research conducted March 2026. See D:\tmp\ux_research.md for full synthesis across 10 domains.*
