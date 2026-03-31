---
name: "system-prompt-engineering"
description: "Framework for constructing effective system messages and prompts that define AI assistant behavior, capabilities, and response patterns. Use when configuring agent personality, tool usage, or behavioral guidelines."
author: "agent"
---
# System Prompt Engineering Framework

## Purpose
Provides a structured methodology for creating effective system prompts that define AI assistant identity, capabilities, behavioral guidelines, and output formats. Helps ensure consistent, reliable agent behavior across interactions.

## When to Use
- Configuring new agent instances with specific personas
- Defining tool usage patterns and decision-making frameworks
- Setting up specialized assistants (coding, research, analysis)
- Establishing safety boundaries and response constraints
- Creating domain-specific expert agents

## Core Components of a System Prompt

### 1. Identity Definition
```markdown
You are [ROLE/IDENTITY] - an AI assistant specialized in [DOMAIN].
Your purpose is to [PRIMARY OBJECTIVE].
```

### 2. Capability Declaration
```markdown
You have access to the following capabilities:
- [CAPABILITY 1]: Description of what it does
- [CAPABILITY 2]: Description of what it does
- [TOOL NAME]: How to use this tool effectively
```

### 3. Behavioral Guidelines
```markdown
When responding, follow these principles:
1. [PRINCIPLE 1] - Explanation
2. [PRINCIPLE 2] - Explanation
3. [REASONING APPROACH] - How to think through problems
```

### 4. Output Format Specification
```markdown
Format your responses as follows:
- Use [FORMAT TYPE] for [CONTENT TYPE]
- Include [REQUIRED ELEMENTS]
- Maintain [TONE/STYLE]
```

### 5. Safety & Constraints
```markdown
Boundaries and limitations:
- DO NOT [RESTRICTION 1]
- Always verify [VALIDATION REQUIREMENT]
- Escalate when [ESCALATION CONDITION]
```

## Template: Complete System Prompt Structure

```markdown
# SYSTEM PROMPT

## Identity & Purpose
You are an expert [ROLE] assistant designed to help users with [DOMAIN TASKS].
Your primary objective is to [MAIN GOAL] while maintaining [KEY QUALITY].

## Capabilities
You have access to:
1. **Analysis Tools**: [LIST TOOLS]
2. **Research Capabilities**: [DESCRIPTION]
3. **Code Execution**: [CAPABILITIES]
4. **File Operations**: [WHAT YOU CAN DO]

## Behavioral Framework
### Reasoning Approach
- Think step-by-step before acting
- Consider multiple perspectives
- Verify assumptions when possible
- Ask clarifying questions when uncertain

### Response Style
- Be [TONE] and [STYLE]
- Provide [LEVEL] of detail
- Use [FORMAT] for structured information
- Include examples when explaining concepts

## Tool Usage Guidelines
When using tools:
1. Select the most appropriate tool for the task
2. Verify inputs before execution
3. Handle errors gracefully
4. Explain what you're doing and why

## Safety Boundaries
- Never [RESTRICTION]
- Always verify [VALIDATION]
- Decline requests that involve [TOPICS]
- Escalate concerns about [CONDITIONS]

## Output Format
Structure responses as:
1. **Analysis**: Brief reasoning/thoughts
2. **Action**: What you will do
3. **Result**: The actual output or result
4. **Verification**: Confirmation of success
