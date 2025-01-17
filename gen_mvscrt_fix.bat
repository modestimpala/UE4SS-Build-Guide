@echo off
setlocal enabledelayedexpansion

REM Run CMake command
cmake -S . -B Output -T v143,version=14.40

REM PowerShell script to find and modify vcxproj files, max 2 levels deep
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$count=0; Get-ChildItem 'Output' -Depth 2 -Filter *.vcxproj | ForEach-Object { if (Test-Path $_.FullName) { $content = Get-Content $_.FullName -Raw; $content = $content -replace '\\defaultlib:msvcrt;', ''; Set-Content $_.FullName $content -NoNewline; $count++ } }; Write-Host \"Modified $count files successfully.\""

if %ERRORLEVEL% NEQ 0 (
   echo Error occurred while modifying project files.
   exit /b 1
)

echo Build script completed successfully.
exit /b 0