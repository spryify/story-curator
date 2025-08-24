# Activate the Python virtual environment
# Usage: .\activate.ps1

Write-Host "Activating Python virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1
Write-Host "Virtual environment activated!" -ForegroundColor Green
Write-Host "Python version: $(python --version)" -ForegroundColor Blue
Write-Host "Virtual environment path: $((Get-Item '.\.venv').FullName)" -ForegroundColor Blue
