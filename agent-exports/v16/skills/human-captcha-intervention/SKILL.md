---
name: human-captcha-intervention
description: 'Browser-based automation encounters a CAPTCHA challenge that cannot
  be solved programmatically. Keywords: "CAPTCHA",...'
triggers:
- 'Browser-based automation encounters a CAPTCHA challenge that cannot be solved programmatically.
  Keywords: "CAPTCHA",...'
version: '1.0'
author: Exocortex
---

# Skill: Human CAPTCHA Intervention

## Trigger
Browser-based automation encounters a CAPTCHA challenge that cannot be solved programmatically. Keywords: "CAPTCHA", "verify you're human", "checkbox verification", "image selection puzzle", "reCAPTCHA", "hCaptcha", "Cloudflare challenge", "browser stuck on verification".

## Inputs Required
- **Page URL** — where the CAPTCHA is blocking progress
- **CAPTCHA type** — checkbox, image selection, text entry, sliding puzzle, etc.
- **Screenshot path** — visual evidence of the challenge (e.g., `/a0/usr/chats/.../browser/screenshots/*.png`)
- **Task context** — what was being attempted when blocked

## Procedure

### Phase 1: Confirm CAPTCHA Blockage
Before requesting human intervention, verify it's actually a CAPTCHA and not another issue.

1. **Check the page title and visible text:**
   ```bash
   # Look for common CAPTCHA indicators in page content
   grep -i "captcha\|verify.*human\|checkbox\|select all" /path/to/page/source.html 2>/dev/null || echo "No obvious CAPTCHA markers"
   ```

2. **Verify screenshot exists and shows the challenge:**
   ```bash
   ls -la /a0/usr/chats/*/browser/screenshots/*.png | tail -3
   ```

3. **Confirm browser agent hit step limit or explicit error:**
   Check for messages like "Task reached step limit" or "CAPTCHA detected".

### Phase 2: Present CAPTCHA to Human Operator
Format the request clearly so the human can solve it efficiently.

1. **Display the screenshot inline:**
   ```markdown
   ![CAPTCHA Challenge](/a0/usr/chats/<chat_id>/browser/screenshots/<screenshot>.png)
   ```

2. **Provide context in a structured format:**
   ```markdown
   ## CAPTCHA Intervention Required

   **URL:** https://example.com/signup
   **Type:** [ ] reCAPTCHA checkbox  [ ] Image selection  [ ] Text entry  [ ] Other: ___
   **Task blocked:** Email signup for X.com registration
   
   **Instructions:** Please solve the CAPTCHA shown above and provide:
   - If checkbox: Confirm you clicked it
   - If image selection: Describe which images to select (e.g., "traffic lights", "crosswalks")
   - If text entry: Provide the exact characters shown
   ```

3. **Wait for human response** — Do not proceed until operator provides solution.

### Phase 3: Execute Human Solution
Once the operator provides the answer, translate it into browser actions.

1. **For checkbox CAPTCHAs:**
   ```json
   {
     "tool_name": "browser_agent",
     "tool_args": {
       "message": "Click the 'I'm not a robot' checkbox to complete verification, then continue with [original task]."
     }
   }
   ```

2. **For image selection CAPTCHAs:**
   ```json
   {
     "tool_name": "browser_agent",
     "tool_args": {
       "message": "Select all images containing [operator's answer, e.g., 'traffic lights'], then click SUBMIT to verify."
     }
   }
   ```

3. **For text entry CAPTCHAs:**
   ```json
   {
     "tool_name": "browser_agent",
     "tool_args": {
       "message": "Type '[operator's answer]' into the verification field, then submit and continue with [original task]."
     }
   }
   ```

### Phase 4: Verify Success and Resume
Confirm the CAPTCHA was solved and the original task can proceed.

1. **Check for success indicators:**
   - Page navigates forward (URL changes)
   - Form becomes active/submittable
   - No error messages about verification

2. **Resume original task** with updated instructions if needed.

## Quality Checks
- [ ] CAPTCHA actually confirmed before requesting human help (not just step limit hit for other reasons)
- [ ] Screenshot path is correct and accessible to operator
- [ ] CAPTCHA type clearly identified in request to human
- [ ] Human solution translated correctly into browser actions
- [ ] Success verified before resuming original task

## Anti-Patterns
- **Requesting human help without confirming it's a CAPTCHA.** Step limits can be hit for many reasons — slow pages, complex forms, navigation issues. Verify first.
- **Not providing the screenshot.** Humans need to see what they're solving. Always include the image path or embed it.
- **Vague instructions to humans.** "Solve this" is useless. Specify exactly what type of CAPTCHA and what information you need back.
- **Resuming before verification.** If you assume success without checking, you'll loop on the same CAPTCHA again.

## Example Interaction

**Agent:**
```
![CAPTCHA Challenge](/a0/usr/chats/Gg4aZsTw/browser/screenshots/QAefyr6q.png)

## CAPTCHA Intervention Required

**URL:** https://proton.me/mail/signup  
**Type:** reCAPTCHA checkbox ("I'm not a robot")
**Task blocked:** ProtonMail account creation for X.com registration

Please confirm you want me to click the "I'm not a robot" checkbox, or provide alternative instructions.
```

**Human:**
```
Yes, click the checkbox and continue with signup using mountain_7620@proton.me
```

**Agent:** (executes browser_agent with checkbox instruction)
