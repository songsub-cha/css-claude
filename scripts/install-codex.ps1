<#
.SYNOPSIS
  Install CSS into OpenAI Codex (~/.codex runtime + ~/.agents/skills skills).
  The Claude Code install is untouched (use scripts\install.ps1 for that).
.PARAMETER SourcePath
  Path to the css-claude repo. Defaults to the repo containing this script.
.PARAMETER Force
  Overwrite an existing config.json.
.EXAMPLE
  .\scripts\install-codex.ps1
  .\scripts\install-codex.ps1 -Force
#>
[CmdletBinding()]
param([string]$SourcePath = "", [switch]$Force)

if (-not $SourcePath) {
  $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
  $SourcePath = Join-Path $scriptDir ".."
}
$ErrorActionPreference = "Stop"
function Write-Section($m) { Write-Host ""; Write-Host "=== $m ===" -ForegroundColor Cyan }

Write-Section "Verifying prerequisites"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { Write-Host "  [MISSING] python (required to transform sources)" -ForegroundColor Red; exit 1 }
Write-Host "  [OK] $($python.Source)" -ForegroundColor Green
if (Get-Command codex -ErrorAction SilentlyContinue) { Write-Host "  [OK] codex CLI" -ForegroundColor Green } else { Write-Host "  [WARN] codex CLI not found (runtime dependency)" -ForegroundColor Yellow }

$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
$skillsDir = Join-Path $env:USERPROFILE ".agents\skills"

Write-Section "Installing CSS Codex artifacts"
$toolsDir = Join-Path $SourcePath "tools"
$argsList = @("-m", "codex_install", "--source", $SourcePath, "--dest", $codexHome, "--skills-dir", $skillsDir)
if ($Force) { $argsList += "--force" }
Push-Location $toolsDir
try { & $python.Source @argsList } finally { Pop-Location }

Write-Section "Done"
Write-Host "Optional — enable parallel specialists in $codexHome\config.toml:"
Write-Host "  [features]"
Write-Host "  multi_agent = true"
Write-Host ""
Write-Host 'Try: $css-ship "<small idea>" in a new Codex App or CLI session.'
