<#
.SYNOPSIS
  Install CSS (Claude Super System) commands and agents into the user's Claude Code config.

.PARAMETER SourcePath
  Path to the cloned css-claude repo. Defaults to the repo containing this script.

.PARAMETER Force
  Overwrite existing default config (commands/agents are always refreshed).

.EXAMPLE
  .\scripts\install.ps1
  .\scripts\install.ps1 -SourcePath C:\code\css-claude -Force
#>
[CmdletBinding()]
param(
  [string]$SourcePath = "",
  [switch]$Force
)

# $PSScriptRoot is empty when invoked via `powershell -File` from an external shell
if (-not $SourcePath) {
  $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
  $SourcePath = Join-Path $scriptDir ".."
}

$ErrorActionPreference = "Stop"

function Write-Section($msg) {
  Write-Host ""
  Write-Host "=== $msg ===" -ForegroundColor Cyan
}

function Test-Prereq($name, $check, $hint) {
  if (& $check) {
    Write-Host "  [OK] $name" -ForegroundColor Green
  } else {
    Write-Host "  [MISSING] $name" -ForegroundColor Red
    Write-Host "    $hint" -ForegroundColor Yellow
    return $false
  }
  return $true
}

Write-Section "Verifying prerequisites"

$ok = $true
$ok = (Test-Prereq "git" { (Get-Command git -ErrorAction SilentlyContinue) -ne $null } "Install git for Windows: https://git-scm.com/download/win") -and $ok
$ok = (Test-Prereq "gh CLI" { (Get-Command gh -ErrorAction SilentlyContinue) -ne $null } "Install gh: winget install GitHub.cli") -and $ok

$claudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$ok = (Test-Prereq "Claude config dir ($claudeHome)" { Test-Path $claudeHome } "Run Claude Code at least once to create $claudeHome") -and $ok

if (-not $ok) {
  Write-Host ""
  Write-Host "Aborting: fix the missing prerequisites above and re-run." -ForegroundColor Red
  exit 1
}

# superpowers warning (non-fatal)
$settingsPath = Join-Path $claudeHome "settings.json"
if (Test-Path $settingsPath) {
  $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
  $sp = $settings.enabledPlugins.'superpowers@claude-plugins-official'
  if (-not $sp) {
    Write-Host "  [WARN] superpowers plugin not enabled in settings.json" -ForegroundColor Yellow
    Write-Host "         CSS depends on it. Enable via /plugin or edit settings.json." -ForegroundColor Yellow
  } else {
    Write-Host "  [OK] superpowers plugin enabled" -ForegroundColor Green
  }
}

Write-Section "Creating directories"
$cmdDir   = Join-Path $claudeHome "commands\css"
$agentDir = Join-Path $claudeHome "agents\css"
$cssDir   = Join-Path $claudeHome "css"
New-Item -ItemType Directory -Force -Path $cmdDir, $agentDir, $cssDir | Out-Null
Write-Host "  $cmdDir"
Write-Host "  $agentDir"
Write-Host "  $cssDir"

Write-Section "Copying commands"
$srcCmd = Join-Path $SourcePath "commands"
$cmdFiles = Get-ChildItem $srcCmd -Filter "*.md" -ErrorAction SilentlyContinue
foreach ($f in $cmdFiles) {
  Copy-Item $f.FullName -Destination $cmdDir -Force
  Write-Host "  $($f.Name)"
}
Write-Host "  ($($cmdFiles.Count) command files copied)"

Write-Section "Copying agents"
$srcAgent = Join-Path $SourcePath "agents"
$agentFiles = Get-ChildItem $srcAgent -Filter "*.md" -ErrorAction SilentlyContinue
foreach ($f in $agentFiles) {
  Copy-Item $f.FullName -Destination $agentDir -Force
  Write-Host "  $($f.Name)"
}
Write-Host "  ($($agentFiles.Count) agent files copied)"

Write-Section "Installing default config"
$srcConfig = Join-Path $SourcePath "config\default-config.json"
$dstConfig = Join-Path $cssDir "config.json"
if ((Test-Path $dstConfig) -and -not $Force) {
  Write-Host "  [SKIP] $dstConfig already exists (use -Force to overwrite)" -ForegroundColor Yellow
} else {
  Copy-Item $srcConfig -Destination $dstConfig -Force
  Write-Host "  $dstConfig"
}

Write-Section "Done"
Write-Host "Installed:"
Write-Host "  $($cmdFiles.Count) commands in $cmdDir"
Write-Host "  $($agentFiles.Count) agents   in $agentDir"
Write-Host "  config at        $dstConfig"
Write-Host ""
Write-Host "Try: /css:ship `"<small idea>`" in a sample project."
