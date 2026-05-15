@echo off
title EXOCORTEX SYSTEM MONITOR
mode con: cols=76 lines=42
color 0C
C:\Users\Jake\miniconda3\python.exe "%~dp0monitor.py" %*
pause
