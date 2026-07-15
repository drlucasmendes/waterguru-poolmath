param(
    [string]$RepoName = "waterguru-poolmath"
)

$ErrorActionPreference = "Stop"
$GitHubUser = "drlucasmendes"
$RemoteUrl = "https://github.com/$GitHubUser/$RepoName.git"

Write-Host "Preparing repository for $RemoteUrl"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed or not available in PATH."
}

if (-not (Test-Path ".\custom_components\waterguru_poolmath\manifest.json")) {
    throw "Run this script from the repository root."
}

if (-not (Test-Path ".git")) {
    git init
}

git add .
git commit -m "Initial release"
git branch -M main

$existingRemote = git remote 2>$null | Select-String "^origin$"
if ($existingRemote) {
    git remote set-url origin $RemoteUrl
} else {
    git remote add origin $RemoteUrl
}

Write-Host ""
Write-Host "Next command:"
Write-Host "git push -u origin main"
Write-Host ""
Write-Host "Make sure the empty public GitHub repository already exists:"
Write-Host "https://github.com/$GitHubUser/$RepoName"
