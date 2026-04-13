param(
    [string]$SmtpUser = "floodguardindia@gmail.com",
    [string]$SmtpPass = "cvxwyxylkjulsehb",
    [string]$SmtpFrom = "floodguardindia@gmail.com",
    #[string]$TwilioFrom = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root "local.env.ps1"

if (-not (Test-Path $envFile)) {
    throw "local.env.ps1 not found. Create it first."
}

$content = Get-Content $envFile -Raw

function Get-CurrentEnvValue {
    param([string]$Name)
    $pattern = '(?m)^\$env:' + [regex]::Escape($Name) + '\s*=\s*"([^"]*)"\s*$'
    $m = [regex]::Match($script:content, $pattern)
    if ($m.Success) { return $m.Groups[1].Value }
    return ""
}

function Set-EnvLine {
    param([string]$Name, [string]$Value)
    $escaped = $Value.Replace('"', '\"')
    $pattern = '(?m)^\$env:' + [regex]::Escape($Name) + '\s*=\s*"[^"]*"\s*$'
    $replacement = "`$env:$Name = ""$escaped"""
    if ([regex]::IsMatch($script:content, $pattern)) {
        $script:content = [regex]::Replace($script:content, $pattern, $replacement)
    } else {
        $script:content += "`r`n$replacement"
    }
}

if (-not $SmtpUser) { $SmtpUser = Get-CurrentEnvValue "SMTP_USER" }
if (-not $SmtpPass) { $SmtpPass = Get-CurrentEnvValue "SMTP_PASS" }
if (-not $SmtpFrom) { $SmtpFrom = Get-CurrentEnvValue "SMTP_FROM" }
if (-not $TwilioFrom) { $TwilioFrom = Get-CurrentEnvValue "TWILIO_FROM" }

if (-not $SmtpUser) { $SmtpUser = Read-Host "Enter SMTP_USER (example: your_email@gmail.com)" }
if (-not $SmtpPass) { $SmtpPass = Read-Host "Enter SMTP_PASS (Gmail app password)" }
if (-not $SmtpFrom) { $SmtpFrom = Read-Host "Enter SMTP_FROM (example: FloodGuard <your_email@gmail.com>)" }

Set-EnvLine -Name "SMTP_USER" -Value $SmtpUser
Set-EnvLine -Name "SMTP_PASS" -Value $SmtpPass
Set-EnvLine -Name "SMTP_FROM" -Value $SmtpFrom
Set-EnvLine -Name "TWILIO_FROM" -Value $TwilioFrom

Set-Content -Path $envFile -Value $content
Write-Host "Updated local.env.ps1 successfully."
