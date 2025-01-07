@echo off
setlocal

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.9 or higher.
    pause
    exit /b 1
)

:: Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo Error installing uv!
        pause
        exit /b 1
    )
)

:: Install dependencies
echo Installing dependencies...
uv sync
call .venv\Scripts\activate.bat

:: Create launcher script
echo Creating launcher script...
(
    echo Set WS = CreateObject^("WScript.Shell"^)
    echo Set FSO = CreateObject^("Scripting.FileSystemObject"^)
    echo strScriptPath = FSO.GetParentFolderName^(WScript.ScriptFullName^)
    echo WS.CurrentDirectory = strScriptPath
    echo WS.Run """" ^& strScriptPath ^& "\.venv\Scripts\python.exe"" """ ^& strScriptPath ^& "\main.py""", 0, False
) > vimouse.vbs

:: Create shortcuts using PowerShell
echo Creating shortcuts...
powershell -ExecutionPolicy Bypass -Command "$desktop = [Environment]::GetFolderPath('Desktop'); $startup = (New-Object -ComObject WScript.Shell).SpecialFolders('Startup'); $proj = '%CD%'; $vbs = Join-Path $proj 'vimouse.vbs'; $icon = Join-Path $proj 'icon_256x256.ico'; foreach ($path in @($desktop, $startup)) { $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut([IO.Path]::Combine($path, 'ViMouse.lnk')); $shortcut.TargetPath = 'C:\Windows\System32\wscript.exe'; $shortcut.Arguments = '""' + $vbs + '""'; $shortcut.WorkingDirectory = $proj; $shortcut.IconLocation = $icon; $shortcut.Save(); }"

echo.
echo Installation completed!
echo The application has been added to startup and a desktop shortcut has been created.
pause 