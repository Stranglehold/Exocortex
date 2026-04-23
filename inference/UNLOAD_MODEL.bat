@echo off
echo Unloading model to free VRAM...
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8080/v1/model/unload' -Method Post"
echo.
echo VRAM freed. Run LOAD_MODEL.bat to reload when done gaming.
pause
