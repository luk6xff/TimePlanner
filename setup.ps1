$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir "venv"

if (Test-Path $VenvDir -PathType Container) {
    Write-Host "Directory $VenvDir exists."
} else {
    Write-Host "Error: Directory $VenvDir does not exist. Installing new venv..."
    Set-Location $ScriptDir
    python -m venv venv
}