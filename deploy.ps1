$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir "venv"

function Activate-VirtualEnvironment {
    $VenvPath = Join-Path $VenvDir "Scripts\Activate"
    if (Test-Path $VenvPath) {
        & $VenvPath
    } else {
        Write-Host "Error: Virtual environment not found. Please run 'python -m venv venv' to create it."
        Exit 1
    }
}

Activate-VirtualEnvironment
Remove-Item -Path build\* -Force -Recurse
Remove-Item -Path dist\* -Force -Recurse
Remove-Item -Path TimePlanner.exe.spec -Force -Recurse
pyinstaller main.py --onefile --clean --workpath=build --distpath=dist --windowed --name=TimePlanner.exe --icon=media\icon.ico