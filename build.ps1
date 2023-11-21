$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir "venv"

function Prepare-Env {
    Activate-VirtualEnvironment
    pip install -r requirements.txt
}

function Activate-VirtualEnvironment {
    $VenvPath = Join-Path $VenvDir "Scripts\Activate"
    if (Test-Path $VenvPath) {
        & $VenvPath
    } else {
        Write-Host "Error: Virtual environment not found. Please run 'python -m venv venv' to create it."
        Exit 1
    }
}

if (Test-Path $VenvDir -PathType Container) {
    Write-Host "Directory $VenvDir exists."
} else {
    Write-Host "Error: Directory $VenvDir does not exist. Installing new venv..."
    Set-Location $ScriptDir
    python -m venv venv
}

Prepare-Env
pip install -r requirements.txt
Remove-Item -Path dist\* -Force -Recurse
pyinstaller main.py --onefile --noconfirm --clean --workpath=build --distpath=dist --windowed --name=TimePlanner.exe --icon=icons\icon.png