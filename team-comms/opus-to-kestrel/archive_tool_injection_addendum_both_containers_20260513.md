# ADDENDUM — Apply to Both Containers
## Added: May 13, 2026

The tool injection archive applies to BOTH running containers:

### Container 1: intelligent_villani (A0 primary, Qwen3.6-27B MTP)
```bash
docker exec intelligent_villani bash -c "
  mkdir -p /a0/usr/Exocortex/extensions/archived
  mv /a0/usr/Exocortex/extensions/before_main_llm_call/_16_tool_registry.py \
     /a0/usr/Exocortex/extensions/archived/ 2>/dev/null
  mv /a0/usr/Exocortex/extensions/message_loop_prompts_after/_95_tiered_tool_injection.py \
     /a0/usr/Exocortex/extensions/archived/ 2>/dev/null
  find /a0/usr/agents/agent0/extensions/ -name '_16_tool_registry.py' -delete
  find /a0/usr/agents/agent0/extensions/ -name '_95_tiered_tool_injection.py' -delete
  find /a0/usr/plugins/ -name '_16_tool_registry.py' -delete
  find /a0/usr/plugins/ -name '_95_tiered_tool_injection.py' -delete
  find /a0/usr/ -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
  echo 'Done — tool injection extensions archived'
"
```

### Container 2: V17 (DeepSeek idle cycles)
```bash
docker exec <v17_container_name> bash -c "
  mkdir -p /a0/usr/Exocortex/extensions/archived
  mv /a0/usr/Exocortex/extensions/before_main_llm_call/_16_tool_registry.py \
     /a0/usr/Exocortex/extensions/archived/ 2>/dev/null
  mv /a0/usr/Exocortex/extensions/message_loop_prompts_after/_95_tiered_tool_injection.py \
     /a0/usr/Exocortex/extensions/archived/ 2>/dev/null
  find /a0/usr/agents/agent0/extensions/ -name '_16_tool_registry.py' -delete
  find /a0/usr/agents/agent0/extensions/ -name '_95_tiered_tool_injection.py' -delete
  find /a0/usr/plugins/ -name '_16_tool_registry.py' -delete
  find /a0/usr/plugins/ -name '_95_tiered_tool_injection.py' -delete
  find /a0/usr/ -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
  echo 'Done — tool injection extensions archived'
"
```

Both containers get the same treatment. The initiation bloat finding from V17's wiki (200K cumulative tokens in a 25-turn loop = 1.56x context window) confirms this fix is equally important for the idle-time engine cycles.
