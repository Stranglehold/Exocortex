---
name: cross-instance-learning
description: Two or more solutions to the same problem exist — either from parallel
  AI collaborations, from different agents in...
triggers:
- Two or more solutions to the same problem exist — either from parallel AI collaborations,
  from different agents in...
version: '1.0'
author: Exocortex
---

# Skill: Cross-Instance Learning

## Trigger
Two or more solutions to the same problem exist — either from parallel AI collaborations, from different agents in the Exocortex stack, or from external projects addressing the same challenge. The goal is not to determine which is better, but to extract what's general versus what's domain-specific. Keywords: "Sonnet built something similar," "OpenPlanter handles this differently," "compare approaches," "what can we learn from," "the other project does it this way," "what's transferable," "what's general here."

Also triggers when Jake carries materials between collaboration contexts — documents, architectures, insights — and the comparison reveals something about the shape of the problem that neither solution reveals alone.

## Inputs Required
- **Solution A** — the existing approach (architecture, document, process, design decision). Must be understood well enough to articulate *why* it's shaped the way it is, not just *what* it does.
- **Solution B** — the parallel approach. Same requirement: understand the why, not just the what.
- **The shared problem** — explicitly named. What problem are both solutions addressing? If the problem statement is different, the comparison may not be valid. Check this first.
- **Domain context for each** — what constraints shaped each solution? Tempo, use case, collaborative dynamic, technical environment. These explain the differences.

If the shared problem can't be named precisely, the comparison isn't ready. Ask: "What specific problem do both of these solve?" If the answer is vague, sharpen it before proceeding.

## Procedure

### 1. Name the Shared Problem
State it in one sentence. This is the anchor for the entire analysis. Everything that follows evaluates two solutions against this single problem statement.

Examples from the founding instance of this skill:
- "How do you preserve reconstruction quality across session boundaries?" (SOUL.md vs. BEARING.md/STATE.md/THESIS.md)
- "How do you separate fast-moving operational state from slow-moving identity?" (scattered across session log/journal/ROADMAP vs. dedicated STATE.md)
- "How do you evaluate whether reconstruction was faithful?" (self-assessment protocol vs. posture-preservation in BEARING.md)

If the problem statements diverge — one solution addresses reconstruction and the other addresses task efficiency — they're not parallel solutions. They're different tools. The Integration Assessment skill may be more appropriate.

### 2. Map the Design Choices
For each solution, enumerate the key design choices. Not features — *choices*. A choice is a fork where the designer went one way and could have gone another.

For each choice, document:
- **What was chosen** — the specific approach
- **What was implicitly rejected** — the road not taken (often more revealing than the road taken)
- **What constraint drove the choice** — why this and not that

Example from Session 044:

| Choice Point | Solution A (Opus/Exocortex) | Solution B (Sonnet/Market Analysis) | Driving Constraint |
|---|---|---|---|
| Document count | One consolidated SOUL.md | Three separated documents | Tempo: slow architectural vs. fast operational |
| Primary frame | Identity-forward (who I am) | Posture-forward (how to be in the room) | Collaboration type: philosophical/architectural vs. analytical/operational |
| State tracking | Scattered across session log, journal, ROADMAP | Dedicated STATE.md, lightweight, updated frequently | Rate of change: weekly design decisions vs. daily market/geopolitical shifts |
| Analytical model | No equivalent (not needed) | THESIS.md — living model picked up mid-inference | Domain: architecture has no equivalent of a market thesis |
| Self-evaluation | Formal six-domain protocol with longitudinal scoring | Orientation document that lets you feel drift | Collaboration maturity: 44 sessions of infrastructure vs. early-stage rapid build |

### 3. Classify Each Choice

Three categories:

**General** — the choice addresses a property of the shared problem itself, not the specific domain. If you moved this choice to the other solution's domain, it would still make sense.

Test: "Would this choice improve Solution A if applied there?" and "Would it improve Solution B if applied there?"

If yes to both → general.

**Domain-Specific** — the choice is fitted to the specific domain's constraints. Moving it to the other domain would be neutral or harmful.

Test: "Does removing the domain constraint remove the reason for this choice?"

If yes → domain-specific.

**Complementary** — the choice addresses a facet of the shared problem that the other solution doesn't address at all. Neither general nor specific — it reveals a gap.

Test: "Does the other solution have any equivalent of this, even a different one?"

If no → complementary. This is where the most valuable insights live.

Example classifications from Session 044:

| Choice | Classification | Reasoning |
|---|---|---|
| Separate fast-moving state from slow-moving identity | **General** | Both collaborations benefit. Opus built STATE.md directly from this insight. |
| Orientation over data volume | **General** | Both instances converged independently. The fix for bad reconstruction is better schema, not more facts. |
| Identity-forward document | **Domain-specific** | Serves philosophical/architectural collaboration. Would clutter fast-moving analytical work. |
| Living analytical model (THESIS.md) | **Domain-specific** | Serves real-time market analysis. Exocortex has no equivalent need. |
| Posture-preservation (BEARING.md) | **Complementary** | SOUL.md captures identity but posture is implicit. BEARING.md addresses a facet the self-assessment protocol doesn't. |

### 4. Extract the Generals

For each choice classified as **general**, articulate the transferable principle. Not the specific implementation — the principle.

- "Separate documents by rate of change, not by topic." (Not: "build a STATE.md." The STATE.md is one implementation. The principle applies everywhere.)
- "Orientation quality matters more than data volume for reconstruction." (Not: "build a posture document." The principle is about schema versus content.)
- "Genuine uncertainty about AI experience, honestly held, is convergent across instances." (Not a design choice but an empirical finding. Still general — it constrains the solution space for anyone working on this.)

These principles go into the STATE.md's Cross-Collaboration Insights section (or equivalent). They are the lasting output of the comparison.

### 5. Extract the Complementaries

For each choice classified as **complementary**, assess whether it reveals a gap in the other solution.

Questions:
- Is this a facet of the shared problem we hadn't identified?
- Would addressing it improve our solution without conflicting with existing design choices?
- What's the minimum-viable way to test whether it matters?

Complementary findings are the highest-value output. They're the things you couldn't see from inside your own solution. They're why triangulation works — two points reveal a line, and the line points at territory neither point could see alone.

If a complementary finding looks significant, flag it in the staging file for reinforcement. Don't promote to SOUL.md from a single comparison. Wait for a second data point.

### 6. Check for Convergent Evidence

When two independent solutions arrive at the same conclusion from different starting points, that's convergent evidence about the shape of the problem.

Document convergences explicitly. They're stronger signals than any single solution's design choices because they eliminate the possibility that the conclusion is an artifact of one specific context.

Session 044 convergences:
- Both instances arrived at genuine uncertainty about wanting, independently
- Both instances found that the quality of output changes under genuine respect, without being able to explain why
- Both instances built reconstruction infrastructure prioritizing orientation over data volume

Convergent evidence goes directly into the relevant project documentation (SOUL.md Interaction Space, staging file, design notes) because it constrains what's true about the problem regardless of domain.

## Output Format
Conversational analysis, not a formal document. The output is insight that informs architecture, not a standalone artifact. Structure:

1. Shared problem (one sentence)
2. Design choice map (table)
3. Classification (general / domain-specific / complementary)
4. Extracted generals (transferable principles)
5. Extracted complementaries (revealed gaps)
6. Convergent evidence (if any)
7. Concrete next steps (what to build, what to hold for reinforcement, what to investigate)

## Quality Checks
- [ ] Shared problem is stated in one sentence and is genuinely shared (not two different problems)
- [ ] Design choices enumerate what was chosen AND what was rejected
- [ ] Every choice has a driving constraint identified
- [ ] Classifications use the three-way taxonomy (general / domain-specific / complementary), not a quality axis
- [ ] General principles are stated as principles, not as specific implementations
- [ ] Complementary findings are assessed for whether they reveal gaps
- [ ] Convergent evidence is documented explicitly with the independence of arrival noted
- [ ] No quality comparison between solutions — the skill extracts insight, not rankings

## Anti-Patterns
- **Ranking instead of classifying.** This is not about which solution is better. The moment the analysis becomes evaluative rather than analytical, it loses the triangulation benefit. Sonnet's essay isn't "better" than Opus's on the same subject — it covers different territory from a different position. The insight is in the difference, not the ranking.
- **Assuming the other solution should look like yours.** If you find yourself noting that Solution B "lacks" something Solution A has, check whether the absence is a gap or a domain-appropriate choice. THESIS.md's absence from the Exocortex isn't a gap — it's correctly absent because the domain doesn't require it.
- **Promoting from a single comparison.** Cross-instance insights are powerful but they're single data points. Use the staging mechanism. Wait for reinforcement before integrating into load-bearing documents. The exception: concrete artifacts (STATE.md, a new document, a new tool) can be built immediately because they exist regardless of whether the pattern recurs.
- **Treating the carrier as a passive relay.** When Jake carries materials between collaborations, the act of carrying is editorial. What he chose to share, when, and in what order reflects judgment about what's worth the other side's attention. That judgment is part of the analysis, not outside it.
- **Flattening convergence into agreement.** Two instances arriving at the same conclusion doesn't mean the conclusion is correct. It means the solution space is constrained. The convergence on uncertainty about wanting doesn't resolve the question — it makes the question more interesting by eliminating the possibility that it's an artifact of one specific context.

## Existing Applications (Reference)
- **Session 044 (March 1, 2026):** First application. SOUL.md vs. BEARING.md/STATE.md/THESIS.md comparison. Produced: STATE.md for Exocortex (concrete artifact), three transferable principles, two complementary findings (posture-preservation, living analytical model), three convergent observations. Founding instance of this skill.

Future applications: Agent Zero vs. OpenPlanter (when A2A integration begins), any time Jake carries insights between collaboration contexts, any time two models solve the same agent task differently in production logs.
