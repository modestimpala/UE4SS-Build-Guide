@echo off
setlocal

echo Running first submodule update...
for /f "delims=" %%a in ('git submodule update --init --recursive') do (
    echo %%a
)

cd .\RE-UE4SS\
echo Running second submodule update in RE-UE4SS directory...
for /f "delims=" %%a in ('git submodule update --init --recursive') do (
    echo %%a
)

pause