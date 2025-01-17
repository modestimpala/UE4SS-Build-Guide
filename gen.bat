@echo off
setlocal enabledelayedexpansion

REM Run CMake command
cmake -S . -B Output -T v143,version=14.40


echo Build script completed successfully.
exit /b 0