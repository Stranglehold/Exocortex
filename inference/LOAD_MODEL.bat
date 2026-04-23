@echo off
echo Loading model into VRAM...
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8080/v1/model/load' -Method Post"
echo.
echo Model loaded. Agent Zero ready.
pause
