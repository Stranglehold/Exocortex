@echo off
REM Exocortex Attention Router (BP-01) — daily digest wrapper.
REM Fired by the Windows Task Scheduler job "Exocortex Attention Router".
REM Runs the router with its 24h default window; the router delivers ONE digest
REM into team-comms/inbox/jake/. Output is appended to attention_router.log.
REM
REM Recreate the daily schedule (08:00, runs when Jake is logged on). Since 2026-09-12 the task
REM runs this file through the hidden launcher, so no console window opens; the router's exit
REM code passes through (3 = Docker off, digest delivered as UNVERIFIED):
REM   schtasks /create /tn "Exocortex Attention Router" ^
REM     /tr "wscript.exe //B //Nologo \"D:\Vibecode\Agent-Zero\Exocortex\scripts\run_hidden.vbs\" ^
REM          \"D:\Vibecode\Agent-Zero\Exocortex\monitor\attention_router.log\" ^
REM          \"D:\Vibecode\Agent-Zero\Exocortex\monitor\run_attention_router.bat\"" ^
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
set "RC=%errorlevel%"
REM Redirection first: "echo Exit: 3>> log" would make cmd read the digit as a file handle, and the
REM Exit line landed on the console, empty, since the file was written (2026-09-13).
>> "%LOG%" echo Exit: %RC%
REM Pass the router's exit code out of the batch (2026-09-13): it used to end on the echo above, so the
REM scheduler saw 0 whatever the router did. endlocal & exit expands RC before endlocal discards it.
endlocal & exit /b %RC%
