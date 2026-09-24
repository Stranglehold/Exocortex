#!/bin/bash
# Controls for the retirement gate in scripts/install_exocortex_plugin.sh.
# Runs the REAL script against a scratch copy of the repo, with a fake `docker` that only
# records its arguments. Nothing reaches a container.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SP="$(mktemp -d)"
W="$SP/walkgate"
pass=0; fail=0
ok()  { echo "  PASS  $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL  $1"; fail=$((fail + 1)); }

fresh() {
  rm -rf "$W"; mkdir -p "$W/repo/scripts" "$W/bin"
  cp "$REPO/scripts/install_exocortex_plugin.sh" "$REPO/scripts/retired_manifest.txt" \
     "$REPO/scripts/merge_plugin_config.py" "$W/repo/scripts/"
  cp -r "$REPO/plugins" "$W/repo/plugins"
  find "$W/repo/plugins" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  cat > "$W/bin/docker" <<'EOF'
#!/bin/bash
echo "$*" >> "$DOCKER_LOG"
exit 0
EOF
  chmod +x "$W/bin/docker"
  : > "$W/docker.log"
}

run() {  # run the installer; sets RC and OUT
  OUT="$(cd "$W/repo" && PATH="$W/bin:$PATH" DOCKER_LOG="$W/docker.log" CONTAINER=fake \
         bash scripts/install_exocortex_plugin.sh 2>&1)"
  RC=$?
}

ARCH="$REPO/archive/plugins-_exocortex/2026-09-08-prune"
EXT="plugins/_exocortex/extensions/python"

echo "1. negative control: the tree as committed"
fresh; run
[ "$RC" -eq 0 ] && ok "exit 0" || bad "exit $RC"
echo "$OUT" | grep -q "refused   : 0" && ok "refused 0" || bad "refused line: $(echo "$OUT" | grep refused)"
n_cp=$(grep -c '^cp \./.* fake:/a0/usr/plugins/_exocortex/' "$W/docker.log")   # deploy copies only; the config merge adds two cp to /tmp
n_files=$(cd "$W/repo/plugins/_exocortex" && find . -type f ! -name '*.bak' ! -name '*.bak-*' ! -name '*~' | grep -vc 'config/config.json$')
[ "$n_cp" -eq "$n_files" ] && ok "docker cp for every file ($n_cp)" || bad "cp $n_cp vs files $n_files"

echo "2. positive control: a retired file back at its manifest path"
fresh
cp "$ARCH/before_main_llm_call/_11_belief_state_tracker.py" "$W/repo/$EXT/before_main_llm_call/"
run
[ "$RC" -eq 3 ] && ok "exit 3" || bad "exit $RC"
echo "$OUT" | grep -q "REFUSED manifest-path extensions/python/before_main_llm_call/_11_belief_state_tracker.py" \
  && ok "named as manifest-path" || bad "not named: $(echo "$OUT" | grep -i refused)"
grep -q "_11_belief_state_tracker.py" "$W/docker.log" && bad "it was copied anyway" || ok "never copied"
echo "$OUT" | grep -q "RETIRED FILES REFUSED: 1" && ok "summary block" || bad "no summary block"

echo "3. positive control: a retired name moved into another hook"
fresh
cp "$ARCH/before_main_llm_call/_10_session_init.py" "$W/repo/$EXT/message_loop_end/_10_session_init.py"
run
[ "$RC" -eq 3 ] && ok "exit 3" || bad "exit $RC"
echo "$OUT" | grep -q "REFUSED manifest-name extensions/python/message_loop_end/_10_session_init.py" \
  && ok "named as manifest-name" || bad "not named: $(echo "$OUT" | grep -i refused)"
grep -q "_10_session_init.py" "$W/docker.log" && bad "it was copied anyway" || ok "never copied"

echo "4. manifest missing: warns, gate off, deploy proceeds"
fresh; rm "$W/repo/scripts/retired_manifest.txt"; run
[ "$RC" -eq 0 ] && ok "exit 0" || bad "exit $RC"
echo "$OUT" | grep -q "retirement gate is OFF" && ok "warning printed" || bad "no warning"

echo "5. a live file that merely shares a prefix is not refused"
fresh; run
grep -q "_12_proactive_supervisor_logger.py" "$W/docker.log" && ok "_12_proactive_supervisor_logger.py deployed" \
  || bad "_12_proactive_supervisor_logger.py missing from the deploy"

echo
echo "RESULT: $pass passed, $fail failed"
rm -rf "$W"
[ "$fail" -eq 0 ]
