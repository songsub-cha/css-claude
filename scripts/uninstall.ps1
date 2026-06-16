<#
.SYNOPSIS
  Remove CSS commands and agents from the user's Claude Code config.
  Preserves ~/.claude/css/config.json and per-project artifacts.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$claudeHome = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
$cmdDir   = Join-Path $claudeHome "commands\css"
$agentDir = Join-Path $claudeHome "agents\css"
$libDir   = Join-Path $claudeHome "css\lib"

foreach ($d in @($cmdDir, $agentDir, $libDir)) {
  if (Test-Path $d) {
    Remove-Item -Recurse -Force $d
    Write-Host "Removed $d" -ForegroundColor Green
  } else {
    Write-Host "Skip (absent): $d" -ForegroundColor Yellow
  }
}

Write-Host ""
Write-Host "Kept:"
Write-Host "  $(Join-Path $claudeHome 'css\config.json') — your personal defaults"
Write-Host "  <project>/.claude/css/ — per-project artifacts (remove manually if no longer needed)"
Write-Host ""
Write-Host "To reinstall: scripts\install.ps1"
