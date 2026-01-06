# Quick fix script - Delete old models and retrain
# Encoding: UTF-8

chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "Quick Fix: Delete old models and retrain" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Check data format
Write-Host ""
Write-Host "1. Checking data format..." -ForegroundColor Yellow
$firstLine = Get-Content "datasets\linzhi\train.jsonl" -First 1 -Encoding UTF8
$hasSystem = $firstLine -match '"role":\s*"system"'

if ($hasSystem) {
    Write-Host "WARNING: Data still contains system prompt, need to fix" -ForegroundColor Red
    Write-Host "   Run: python fix_overfitting.py" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "OK: Data format is correct (no system prompt)" -ForegroundColor Green
}

# Delete old models
Write-Host ""
Write-Host "2. Deleting old models..." -ForegroundColor Yellow
if (Test-Path "out\lora_linzhi") {
    Remove-Item -Recurse -Force "out\lora_linzhi"
    Write-Host "Deleted: out\lora_linzhi" -ForegroundColor Green
} else {
    Write-Host "Info: out\lora_linzhi does not exist" -ForegroundColor Gray
}

if (Test-Path "out\merged_linzhi") {
    Remove-Item -Recurse -Force "out\merged_linzhi"
    Write-Host "Deleted: out\merged_linzhi" -ForegroundColor Green
} else {
    Write-Host "Info: out\merged_linzhi does not exist" -ForegroundColor Gray
}

# Check Ollama model
Write-Host ""
Write-Host "3. Checking Ollama model..." -ForegroundColor Yellow
try {
    $ollamaList = ollama list 2>&1
    if ($ollamaList -match "linzhi-lora") {
        Write-Host "Found Ollama model: linzhi-lora" -ForegroundColor Yellow
        $confirm = Read-Host "Delete it? (y/N)"
        if ($confirm -match "^[yY]") {
            ollama rm linzhi-lora 2>&1 | Out-Null
            Write-Host "Deleted Ollama model" -ForegroundColor Green
        }
    } else {
        Write-Host "Info: Ollama model not found" -ForegroundColor Gray
    }
} catch {
    Write-Host "Info: Could not check Ollama (Ollama may not be installed)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Cleanup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next step: Run training" -ForegroundColor Cyan
Write-Host "   .\train.ps1 linzhi" -ForegroundColor Yellow

