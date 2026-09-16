' run_hidden.vbs - run a scheduled command with NO console window, append its output to a log, exit with its code.
'
' Fable, 2026-09-12, at Jake's ask. The three Exocortex scheduled tasks (agent sync + reindex every 6 h, agent
' backup every 6 h, attention router daily) ran python.exe or a .bat directly in the interactive session, so a console
' window popped up on every run, once in the middle of a game. Task Scheduler cannot hide a console for an interactive
' task without "run whether user is logged on or not", which needs a stored password. This launcher starts the command
' through WScript.Shell.Run with window style 0 (hidden), waits, and passes the exit code back, so the task's
' "Last Run Result" still means what it meant before.
'
' Usage, as the task's action (program = wscript.exe):
'   //B //Nologo "D:\Vibecode\Agent-Zero\Exocortex\scripts\run_hidden.vbs" "<logfile>" "<exe>" ["<arg>" ...]
' //B suppresses script error dialogs (nothing may pop up). The log directory is created if missing. Each run appends a
' dated header line, then the command's stdout and stderr. Exit code: the command's, or 2 for bad usage.
Option Explicit
Dim sh, fso, args, logFile, logDir, cmd, i, a, rc, q
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set args = WScript.Arguments
If args.Count < 2 Then WScript.Quit 2
q = Chr(34)
logFile = args(0)
logDir = fso.GetParentFolderName(logFile)
If Len(logDir) > 0 And Not fso.FolderExists(logDir) Then fso.CreateFolder logDir
cmd = ""
For i = 1 To args.Count - 1
    a = args(i)
    If InStr(a, " ") > 0 Or InStr(a, "&") > 0 Or InStr(a, "(") > 0 Then a = q & a & q
    cmd = cmd & " " & a
Next
cmd = Mid(cmd, 2)
' cmd.exe /c "<whole line>": the outer pair of quotes makes cmd keep every inner quote intact.
rc = sh.Run("cmd.exe /c " & q & "echo ==== %DATE% %TIME% run_hidden >> " & q & logFile & q & " 2>&1 & " & cmd & " >> " & q & logFile & q & " 2>&1" & q, 0, True)
WScript.Quit rc
