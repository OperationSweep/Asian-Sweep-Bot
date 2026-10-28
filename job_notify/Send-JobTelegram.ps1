<#
.SYNOPSIS
  Telegram notifications for the job-application run on the Windows PC (@BaksAstraBot).
  Same events and rules as telegram_notify.py, for machines without Python.

.DESCRIPTION
  Reads $env:TELEGRAM_BOT_TOKEN (required) and $env:TELEGRAM_CHAT_ID (default 5373117361).
  The token is never printed. A "submitted" event without -Confirmation is sent as
  UNCONFIRMED, never as a success.

.EXAMPLE
  .\Send-JobTelegram.ps1 -Event test
  .\Send-JobTelegram.ps1 -Event submitted -Company "Acme" -Role "IT Ops Lead" -Link "https://..." -Confirmation "Reed: Application sent"
  .\Send-JobTelegram.ps1 -Event failed  -Company "Acme" -Role "..." -Link "..." -Reason "Upload rejected"
  .\Send-JobTelegram.ps1 -Event blocker -Company "Acme" -Role "..." -Link "..." -Reason "Sign in to Totaljobs" -Action "https://www.totaljobs.com/account/signin"
  .\Send-JobTelegram.ps1 -Event summary -Run "28 Oct morning" -Submitted 12 -Failed 1 -Blocked 2 -Skipped 3
#>
param(
  [Parameter(Mandatory)][ValidateSet('test','submitted','failed','blocker','summary')][string]$Event,
  [string]$Company, [string]$Role, [string]$Link, [string]$Board,
  [string]$Confirmation, [string]$Reason, [string]$Action,
  [string]$Run, [int]$Submitted = 0, [int]$Failed = 0, [int]$Blocked = 0, [int]$Skipped = 0,
  [string]$Details, [switch]$DryRun
)

$token = $env:TELEGRAM_BOT_TOKEN
$chat  = if ($env:TELEGRAM_CHAT_ID) { $env:TELEGRAM_CHAT_ID } else { '5373117361' }
function Esc([string]$s) { [System.Net.WebUtility]::HtmlEncode($s) }
$stamp = "<i>$((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm')) UTC</i>"

$job = @()
if ($Company) { $job += "<b>Company:</b> $(Esc $Company)" }
if ($Role)    { $job += "<b>Role:</b> $(Esc $Role)" }
if ($Board)   { $job += "<b>Board:</b> $(Esc $Board)" }
if ($Link)    { $job += "<b>Link:</b> <a href=""$(Esc $Link)"">$(Esc $Link)</a>" }

switch ($Event) {
  'test' { $lines = @("🔔 <b>Test notification</b>", "Job-application alerts from @BaksAstraBot are set up.") }
  'submitted' {
    if ($Confirmation) { $lines = @("✅ <b>Application SUBMITTED (confirmed)</b>") + $job + "<b>Confirmation:</b> $(Esc $Confirmation)" }
    else { $lines = @("❔ <b>Application UNCONFIRMED</b>") + $job + "No confirmation was seen, so this is NOT counted as submitted. Check the portal or inbox." }
  }
  'failed'  { $lines = @("❌ <b>Application FAILED</b>") + $job + "<b>Reason:</b> $(Esc ($(if ($Reason) {$Reason} else {'not given'})))" }
  'blocker' {
    $lines = @("⚠️ <b>Needs your input</b>") + $job + "<b>What's needed:</b> $(Esc ($(if ($Reason) {$Reason} else {'not given'})))"
    if ($Action) { $lines += "<b>Do it here:</b> <a href=""$(Esc $Action)"">$(Esc $Action)</a>" }
  }
  'summary' {
    $title = "📋 <b>Run summary</b>"; if ($Run) { $title += " — $(Esc $Run)" }
    $lines = @($title, "✅ Submitted (confirmed): $Submitted", "❌ Failed: $Failed", "⚠️ Waiting on you: $Blocked", "⏭ Skipped: $Skipped")
    if ($Details) { $lines += (Esc $Details) }
  }
}
$text = (($lines + $stamp) -join "`n")
if ($text.Length -gt 4096) { $text = $text.Substring(0, 4096) }

if ($DryRun) { Write-Output $text; exit 0 }
if (-not $token) { Write-Error "TELEGRAM_BOT_TOKEN is not set."; exit 2 }

$body = @{ chat_id = $chat; text = $text; parse_mode = 'HTML'; disable_web_page_preview = $true } | ConvertTo-Json -Compress
try {
  $resp = Invoke-RestMethod -Method Post -Uri "https://api.telegram.org/bot$token/sendMessage" `
          -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 20
  if ($resp.ok) { Write-Output "Send-JobTelegram: sent ($Event), message_id=$($resp.result.message_id)"; exit 0 }
  Write-Error "Send-JobTelegram: Telegram refused: $($resp.description)"; exit 1
} catch {
  $msg = $_.Exception.Message -replace [regex]::Escape($token), '<TOKEN>'
  if ($_.ErrorDetails.Message) { $msg = ($_.ErrorDetails.Message -replace [regex]::Escape($token), '<TOKEN>') }
  Write-Error "Send-JobTelegram: request failed: $msg"; exit 1
}
