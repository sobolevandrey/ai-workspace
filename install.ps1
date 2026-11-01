# ai-workspace — установщик для Windows / installer for Windows (PowerShell)
#   irm https://raw.githubusercontent.com/sobolevandrey/ai-workspace/main/install.ps1 | iex
#   или / or:  git clone https://github.com/sobolevandrey/ai-workspace $HOME\.ai-workspace; & $HOME\.ai-workspace\install.ps1
$ErrorActionPreference = "Stop"
$Repo   = if ($env:AIW_REPO)   { $env:AIW_REPO }   else { "https://github.com/sobolevandrey/ai-workspace.git" }
$Engine = if ($env:AIW_ENGINE) { $env:AIW_ENGINE } else { Join-Path $HOME ".ai-workspace" }

function Has($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Install-Winget($id) {
  if (-not (Has winget)) { throw "winget not found. Install 'App Installer' from Microsoft Store, then re-run." }
  winget install --id $id -e --silent --accept-source-agreements --accept-package-agreements
}
function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host "=== ai-workspace ==="
if (-not (Has git)) { Install-Winget "Git.Git"; Refresh-Path }

$py = $null
if (Has py) { $py = @("py", "-3") }
elseif ((Has python) -and -not ((Get-Command python).Source -like "*WindowsApps*")) { $py = @("python") }
if (-not $py) { Install-Winget "Python.Python.3.12"; Refresh-Path; $py = @("py", "-3") }

$Yes = $args -contains "--yes"   # --yes: без вопросов (ставит нейросеть)
if (-not (Has npx) -and $Yes) { Install-Winget "OpenJS.NodeJS.LTS"; Refresh-Path }
elseif (-not (Has npx)) {
  $a = Read-Host "Node.js нужен, чтобы Claude Desktop видел твои файлы (MCP). Установить? / Node.js lets Claude Desktop see your files (MCP). Install? [Y/n]"
  if ($a -notmatch '^[nN]') { Install-Winget "OpenJS.NodeJS.LTS"; Refresh-Path }
}

$here = $PSScriptRoot
if ($here -and (Test-Path (Join-Path $here "aiw.py"))) { $Engine = $here }
elseif (Test-Path (Join-Path $Engine ".git")) { git -C $Engine pull --ff-only -q }
else { git clone -q $Repo $Engine }

$exe = $py[0]; $pre = @(); if ($py.Count -gt 1) { $pre = $py[1..($py.Count - 1)] }
& $exe @pre (Join-Path $Engine "aiw.py") setup @args
