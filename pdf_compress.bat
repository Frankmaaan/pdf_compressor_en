@echo off
REM pdf_compress.bat
REM PDF compression tool shortcut script for Windows users

setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║ PDF compression and splitting tool ║
echo ║ Windows WSL interface ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if WSL is available
wsl --status >nul 2>&1
if errorlevel 1 (
    echo error: WSL is not installed or configured correctly
    echo Please install WSL and Ubuntu first, refer to the document: docs\WINDOWS_GUIDE.md
    pause
    exit /b 1
)

REM Check if the project exists in WSL
wsl -e test -d ~/pdf_compressor
if errorlevel 1 (
    echo Copying project to WSL file system...
    wsl -e cp -r /mnt/c/Users/%USERNAME%/Projects/pdf_compressor ~/pdf_compressor
    echo project copied to WSL
)

REM dependency checking tool
echo check dependency tool...
wsl -e bash -c "cd ~/pdf_compressor && python3 main.py --check-deps" >nul 2>&1
if errorlevel 1 (
    echo.
    The echo dependent tools are not installed and are being installed...
    echo This may take a few minutes, please be patient...
    wsl -e bash -c "cd ~/pdf_compressor && chmod +x install_dependencies.sh && ./install_dependencies.sh"
    
    REM Check again
    wsl -e bash -c "cd ~/pdf_compressor && python3 main.py --check-deps" >nul 2>&1
    if errorlevel 1 (
        echo installation failed, please manually run the installation script in WSL
        pause
        exit /b 1
    )
)

The echo tool is ready!

REM If there are no parameters, display help
if "%~1"=="" (
    echo.
    echo usage: pdf_compress.bat [PDF file path] [options]
    echo.
    echo example:
    echo   pdf_compress.bat C:\Documents\test.pdf
    echo   pdf_compress.bat C:\Documents\test.pdf --allow-splitting
    echo   pdf_compress.bat C:\Documents\PDFs --target-size 8.0 --allow-splitting
    echo.
    Available options for echo:
    echo --allow-splitting allows splitting files
    echo --target-size SIZE target size (MB)
    echo --max-splits NUM maximum number of splits
    echo --verbose detailed output
    echo.
    pause
    exit /b 0
)

REM converts the first parameter to a WSL path
set "input_path=%~1"
set "input_path=!input_path:\=/!"
set "input_path=!input_path::=!"
set "wsl_input=/mnt/!input_path!"

REM sets the output directory
set "output_dir=~/pdf_output"

REM build command
set "cmd=cd ~/pdf_compressor && python3 main.py --input '!wsl_input!' --output-dir !output_dir!"

REM adds additional parameters
shift
:parse_args
if "%~1"=="" goto run_command
set "cmd=!cmd! %1"
shift
goto parse_args

:run_command
REM adds default splitting options if not specified by the user
echo !cmd! | findstr /C:"--allow-splitting" >nul
if errorlevel 1 (
    set "cmd=!cmd! --allow-splitting"
)

echo.
echo is processing PDF files...
echo input: %~1
echo output: will be saved in WSL's ~/pdf_output directory
echo.

REM execution command
wsl -e bash -c "!cmd!"

if errorlevel 1 (
    echo.
    echo processing failed, please check the error message
    pause
    exit /b 1
)

echo.
echo processing completed!
echo.

REM asks if you want to copy the output file to Windows
set /p copy_choice="Do you want to copy the output file to Windows? (y/n): "
if /i "%copy_choice%"=="y" (
    set "win_output=%USERPROFILE%\Documents\PDF Compressed Output"
    echo is copying to: !win_output!
    
    REM creates Windows output directory
    if not exist "!win_output!" mkdir "!win_output!"
    
    REM copy files
    wsl -e bash -c "cp ~/pdf_output/* /mnt/c/Users/%USERNAME%/Documents/PDF Compressed Output/ 2>/dev/null || true"
    
    echo file copied to: !win_output!
    explorer "!win_output!"
)

echo.
echo Press any key to exit...
pause >nul