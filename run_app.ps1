$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "Virtual environment not found. Create it first: py -3.12 -m venv .venv"
    exit 1
}

& .\.venv\Scripts\Activate.ps1

if (-not $env:OPENAI_API_KEY) {
    if (Test-Path ".\.env") {
        Get-Content .\.env | ForEach-Object {
            if ($_ -match '^\s*#' -or $_ -trim() -eq '') { return }
            $name, $value = $_ -split '=', 2
            if ($name -eq 'OPENAI_API_KEY') {
                $env:OPENAI_API_KEY = $value.Trim()
            }
        }
    }
}

if (-not $env:OPENAI_API_KEY) {
    Write-Error "OPENAI_API_KEY is missing. Add it to .env or set it in the session."
    exit 1
}

streamlit run app.py
