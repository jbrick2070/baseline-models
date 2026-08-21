# Grounded, CPU-only fleet template diff -- the clean home (operator, 2026-08-21).
# Fail-closed: any missing roster row, parser error, or structural-sentinel
# failure makes the aggregate exit nonzero. Reference bytes are SHA-256-pinned
# to the installed comfyui-workflow-templates-json package.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$python = "C:\Users\jeffr\Documents\ComfyUI\.venv\Scripts\python.exe"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:CUDA_VISIBLE_DEVICES = ""
$env:PYTHONUTF8 = "1"
$env:OTR_TEST_MODE = "1"
$stamp = Get-Date -Format yyyy-MM-dd
& $python (Join-Path $here "tools\diffomatic_fleet.py") --out-dir (Join-Path $here "receipts\$stamp-grounded") @args
exit $LASTEXITCODE
