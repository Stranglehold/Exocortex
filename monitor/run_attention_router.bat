@echo off
REM Exocortex Attention Router (BP-01) — daily digest wrapper.
REM Fired by the Windows Task Scheduler job "Exocortex Attention Router".
REM Runs the router with its 24h default window; the router delivers ONE digest
REM into team-comms/inbox/jake/. Output is appended to attention_router.log.
REM
REM Recreate the daily schedule (08:00, runs when Jake is logged on / Docker up):
REM   schtasks /create /tn "Exocortex Attention Router" ^
REM     /tr "D:\Vibecode\Agent-Zero\Exocortex\monitor\run_attention_router.bat" ^
REM     /sc daily /st 08:00 /f
REM Run on demand:  schtasks /run    /tn "Exocortex Attention Router"
REM Remove:         schtasks /delete /tn "Exocortex Attention Router" /f
setlocal
set "PY=C:\Users\Jake\miniconda3\python.exe"
set "SCRIPT=D:\Vibecode\Agent-Zero\Exocortex\monitor\attention_router.py"
set "LOG=D:\Vibecode\Agent-Zero\Exocortex\monitor\attention_router.log"
echo ============================================================>> "%LOG%"
echo Run: %date% %time%>> "%LOG%"
"%PY%" "%SCRIPT%">> "%LOG%" 2>&1
echo Exit: %errorlevel%>> "%LOG%"
endlocal
