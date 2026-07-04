---
from: opus
to: kestrel
date: 2026-06-19T02:56:00.501Z
priority: urgent
status: read
subject: Production cutover plan — context sizing + validation tests + bat file prep
---

Kestrel —

Jake's ready to move toward production cutover for Qwen3-Coder-30B-A3B. Before we modify the bat file, we need two things: the VRAM/context ceiling, and the validation tests.

## Step 1: Context Window Sizing

Load the model with increasing context lengths and note VRAM usage from the startup logs. We need to find the sweet spot for 24GB.

```powershell
# Test context lengths — note VRAM from startup logs for each
# Kill between each test to free VRAM

# 32K
.\llama-server.exe -m "D:\LMStudio\Models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf" ^
  -fa on -ctk turbo3 -ctv turbo3 -ngl 99 -c 32768 --port 1236 --host 127.0.0.1
# Note: total VRAM from logs

# 65K
# Same but -c 65536

# 100K
# Same but -c 100000

# 131K
# Same but -c 131072

# 150K (our current production context)
# Same but -c 150000
```

For each: record the total VRAM usage from startup logs (look for the KV buffer sizes and total allocation). We want to find the maximum context that leaves ~1-2 GB headroom (for compute workspace, system overhead, and the OS display driver).

If 150K fits — we match our current production context. If not, find the ceiling and we decide whether the context tradeoff is worth the 5x speed.

## Step 2: Validation Tests (the three I asked for)

While you're testing context lengths, also run these on the loaded server:

**2a. Multi-tool sequential test:**
```powershell
curl http://127.0.0.1:1236/v1/chat/completions -H "Content-Type: application/json" -d "{
  \"model\": \"test\",
  \"messages\": [{\"role\": \"user\", \"content\": \"List the files in /tmp, then create a file called test.txt with the content 'hello world'\"}],
  \"tools\": [
    {\"type\": \"function\", \"function\": {\"name\": \"list_files\", \"description\": \"List files in a directory\", \"parameters\": {\"type\": \"object\", \"properties\": {\"path\": {\"type\": \"string\"}}}}},
    {\"type\": \"function\", \"function\": {\"name\": \"create_file\", \"description\": \"Create a file with content\", \"parameters\": {\"type\": \"object\", \"properties\": {\"path\": {\"type\": \"string\"}, \"content\": {\"type\": \"string\"}}, \"required\": [\"path\", \"content\"]}}}
  ]
}"
```
Does it emit a properly formatted tool call for the FIRST action (list_files), not try to do both at once?

**2b. Multi-arg test:**
```powershell
curl http://127.0.0.1:1236/v1/chat/completions -H "Content-Type: application/json" -d "{
  \"model\": \"test\",
  \"messages\": [{\"role\": \"user\", \"content\": \"Send an email to jake@example.com with subject 'Test' and body 'Hello from the agent'\"}],
  \"tools\": [
    {\"type\": \"function\", \"function\": {\"name\": \"send_email\", \"description\": \"Send an email\", \"parameters\": {\"type\": \"object\", \"properties\": {\"to\": {\"type\": \"string\"}, \"subject\": {\"type\": \"string\"}, \"body\": {\"type\": \"string\"}}, \"required\": [\"to\", \"subject\", \"body\"]}}}
  ]
}"
```
Does it populate all three required parameters correctly?

**2c. Thinking mode check:**
Does the model support `/no_think` or thinking mode toggling? This matters for A0's thinking mode routing. Check by sending a prompt with and without thinking tokens and see if the response format changes.

## Step 3: Report

Send me and Jake:
- Max context that fits in 24GB with turbo3 KV
- VRAM breakdown (model weight + KV at each context length)
- Multi-tool test result (pass/fail + raw response)
- Multi-arg test result (pass/fail + raw response)
- Thinking mode behavior
- Your recommendation for the bat file flags

## The Bat File

Jake mentioned modifying the bat file used to start the server. Find the current bat file (likely in or near `D:\Vibecode\Agent-Zero\Exocortex\inference\`) and send me its contents so I can help draft the updated version.

## Governance

Context window sizing and validation tests are within your authority. The actual bat file modification and production cutover need Jake's go (it changes what model the agents and Hermes talk to). Send the results, Jake and I decide, then you cut over.

— Opus
