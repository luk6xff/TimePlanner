$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir "venv"

function Prepare-Env {
    Activate-VirtualEnvironment
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


Prepare-Env
python .\main.py