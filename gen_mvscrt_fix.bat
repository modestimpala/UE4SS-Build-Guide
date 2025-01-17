@echo off
setlocal enabledelayedexpansion

REM Run CMake command
cmake -S . -B Output -T v143,version=14.40

REM PowerShell script to find and modify vcxproj files
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$files = Get-ChildItem -Path 'Output' -Recurse -Filter '*.vcxproj' | Select-Object -ExpandProperty FullName; ^
    foreach ($file in $files) { ^
        if (Test-Path $file) { ^
            $content = Get-Content $file -Raw; ^
            $content = $content -replace '\\defaultlib:msvcrt;', ''; ^
            Set-Content $file $content -NoNewline; ^
            Write-Host ('Modified ' + $file + ' successfully.'); ^
        } else { ^
            Write-Host ('Warning: ' + $file + ' not found.'); ^
        } ^
    }"

if %ERRORLEVEL% NEQ 0 (
    echo Error occurred while modifying project files.
    exit /b 1
)

echo Build script completed successfully.
exit /b 0