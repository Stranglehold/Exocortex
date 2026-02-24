---
name: structural-analysis
description: "Use this skill when analyzing complex systems for hidden dynamics, feedback loops, second-order effects, or structural vs cyclical forces. Triggers include: macro-economic analysis, technology impact assessment, business model vulnerability analysis, system architecture review, policy analysis, risk assessment of interconnected systems, or any situation where the user asks 'what happens next' or 'what are the consequences of X'. Also use when the user is evaluating investments, designing resilient systems, or trying to understand why something that looks good on the surface might have hidden failure modes. This skill teaches structured thinking about complex systems, not domain-specific knowledge."
---

# Structural Analysis

## Overview

Structural analysis is the discipline of looking at a complex system and identifying the dynamics that aren't visible in the headline metrics. It answers: what are the feedback loops, where are the hidden dependencies, what's structural vs cyclical, and where can intervention actually change the trajectory?

This skill emerged from analyzing how technical expertise in one domain (power grid infrastructure, agent architecture, financial markets) transfers to structural insight in others. The same patterns recur: systems that look healthy by traditional metrics while their foundations shift, feedback loops without natural brakes, and the difference between problems that self-correct and problems that accelerate.

## The Core Questions

For any system under analysis, work through these in order:

### 1. What Are The Feedback Loops?

Every complex system contains feedback loops. Identify them explicitly.

**Positive feedback loops** (self-reinforcing — amplify change):
- More X causes more Y, which causes more X
- These accelerate in either direction and have no natural equilibrium
- Example: AI capability improves → companies cut headcount → savings fund more AI → capability improves

**Negative feedback loops** (self-correcting — dampen change):
- More X causes less Y, which causes less X
- These naturally find equilibrium
- Example: Prices rise → demand falls → prices fall

**Critical question: Does this loop have a natural brake?**

A system with positive feedback loops and no natural brake will run until something external stops it or the inputs are exhausted. If you find a self-reinforcing loop, your next job is to find the brake. If you can't find one, that's your finding.

### 2. What's Structural vs. Cyclical?

This is the single most important classification in any system analysis.

**Cyclical:** The cause eventually self-corrects. Overbuilding leads to slowdown, which leads to lower prices, which leads to new building. The system oscillates around an equilibrium.

**Structural:** The cause does not self-correct. The force driving the change continues or accelerates. The system moves to a new equilibrium that may look nothing like the old one.

**How to distinguish:**
- Cyclical: Remove the initial shock and the system returns to baseline
- Structural: Remove the initial shock and the system still doesn't return because the landscape itself has changed

**Why this matters:** Cyclical problems respond to counter-cyclical policy (stimulus in downturns, restraint in booms). Structural problems do not. Applying cyclical solutions to structural problems wastes resources and delays adaptation.

### 3. What Are The Second and Third-Order Effects?

First-order effects are direct and obvious. Second-order effects are the responses to first-order effects. Third-order effects are the responses to second-order effects.

**Method: Walk the chain.**

```
First order: AI replaces some white-collar jobs
  ↓
Second order: Displaced workers move to lower-paying roles
  ↓
Third order: Increased labor supply in service sector compresses wages there too
  ↓
Fourth order: Wage compression across sectors reduces consumer spending
  ↓
Fifth order: Reduced spending pressures more companies to cut costs via AI
  ↓
[Loop detected — feeds back to first order]
```

**At each step, ask:**
- Who responds to this change?
- What is their rational individual response?
- What happens when everyone makes that same rational response simultaneously?

The gap between "individually rational" and "collectively catastrophic" is where most hidden risk lives. Each company cutting headcount to buy AI is rational. The collective result is demand destruction.

### 4. Where Are The Hidden Dependencies?

Systems that appear diversified often share hidden common dependencies.

**Method: Follow the assumptions.**

Every institution, business model, or system design embeds assumptions about the world. Most of these assumptions are invisible because they've been true for so long that nobody questions them.

Examples of assumptions that function as hidden dependencies:
- "White-collar workers will remain employed at roughly their current income level" (mortgage underwriting)
- "Recurring revenue will remain recurring" (SaaS valuation, ARR-backed lending)
- "Human attention is required for commercial transactions" (advertising, intermediation)
- "Friction is constant" (business models built on human cognitive limitations)
- "The labor market always creates new jobs to replace destroyed ones" (every prior industrial transition)

**When the assumption breaks, everything built on it reprices simultaneously.** This is how sector-specific disruption becomes systemic risk — not through contagion, but through shared assumptions.

### 5. Who Is Positioned For The Transition?

Not all analysis should end with "here's what goes wrong." The structural analyst also identifies:

- **Who benefits from the new structure?** Not who benefits from the disruption itself (that's obvious), but who is positioned for the equilibrium that emerges after.
- **What capabilities become more valuable?** When one input becomes abundant, complementary inputs become more scarce and more valuable.
- **Where are the new moats?** If old moats (friction, information asymmetry, habitual intermediation) are dissolving, what replaces them?
- **What's the timeline?** Structural shifts have different speeds in different domains. Digital disruption moves in quarters. Physical infrastructure moves in decades. Policy moves somewhere in between.

## Analytical Frameworks

### The Moat Autopsy

When analyzing whether a business model, institution, or system survives a structural shift:

1. **Name the moat explicitly.** What competitive advantage, institutional inertia, or structural barrier protects this entity?
2. **Classify the moat type:**
   - Friction moat (built on human cognitive limitations — impatience, inertia, complexity aversion)
   - Scale moat (built on capital requirements or network effects)
   - Knowledge moat (built on information asymmetry)
   - Regulatory moat (built on licensing, compliance, legal barriers)
   - Relationship moat (built on trust and human connection)
3. **Stress test against the structural shift.** Does the shift attack this moat type?
4. **Assess timeline.** How quickly does the moat erode?

Friction moats are most vulnerable to AI because AI agents are friction-elimination machines. Scale moats may strengthen (compute advantages compound). Knowledge moats erode when AI democratizes expertise. Regulatory moats persist longest but eventually adapt.

### The Daisy Chain Test

For interconnected systems (financial, supply chain, organizational):

1. **Map the chain.** Who depends on whom? What assumption does each link make about adjacent links?
2. **Identify the correlated bet.** Are multiple links betting on the same underlying assumption?
3. **Stress the shared assumption.** What happens to the chain if that assumption breaks?
4. **Assess visibility.** Can participants in the chain see the correlation, or is it hidden by layers of indirection?

The most dangerous daisy chains are invisible — where the correlation only becomes apparent after the stress event.

### The Framework Fitness Test

When existing analytical frameworks produce contradictory or nonsensical results:

1. **Identify the framework's embedded assumptions.** Every metric, model, and methodology was designed for a specific context.
2. **Check if those assumptions still hold.** GDP assumes output flowing through wages. Employment rate assumes humans performing work. Productivity assumes human labor as the denominator.
3. **If the assumptions have broken, the framework is producing noise, not signal.** Don't force new reality into old frameworks. Build new ones.

Example: "Ghost GDP" — output that appears in national accounts but never circulates through the real economy because it's generated by compute, not labor. Traditional GDP metrics say the economy is growing. The lived experience says otherwise. The framework is measuring something real (output) but missing something critical (distribution).

## Application to Agent Architecture

Structural analysis applies directly to AI system design:

### System Resilience Analysis
- Map the feedback loops in your agent pipeline
- Identify single points of failure
- Find hidden dependencies (all agents depending on same model server, same memory store, same network connection)
- Classify failures as cyclical (retry and it works) vs structural (fundamental incompatibility)

### Authority Boundary Design  
- What assumptions does each authority level embed?
- If model capability suddenly improves or degrades, do the boundaries still make sense?
- Where are the correlated bets (multiple subsystems assuming model reliability)?

### Cost Structure Analysis
- Which costs are structural (present regardless of activity level) vs cyclical (scale with usage)?
- Where are the hidden token costs (verbose outputs, unnecessary context loading, redundant reasoning)?
- What feedback loops exist in the cost structure (more tasks → more memory → more context → more tokens per task)?

## Principles

1. **The headline metric is always the last to know.** GDP, unemployment rate, stock price — these are lagging indicators of structural change. By the time they confirm the shift, the shift is well underway.

2. **Individually rational, collectively catastrophic.** When analyzing any system with many independent actors, always ask what happens when they all make the same rational choice simultaneously.

3. **You cannot un-invent something.** Once a capability exists, the analysis must account for its existence. "What if we just didn't use AI" is not a valid scenario for structural analysis because the competitive pressure makes adoption inevitable.

4. **Structural shifts don't ask permission.** Public resistance shapes the trajectory and timeline, but does not reverse the underlying capability change. The question is not "will this happen" but "what form does the adaptation take."

5. **The transition is the dangerous part.** The new equilibrium may be better than the old one. The path between them is where the risk concentrates. Analyze the transition, not just the endpoints.

6. **History rhymes but doesn't repeat.** Prior technological transitions provide pattern templates, not predictions. The key analytical question is: what's different this time that might break the historical pattern?

7. **Follow the assumptions, not the narrative.** Every optimistic and pessimistic narrative is built on assumptions. Find the assumptions. Test them. That's where the real analysis lives.
