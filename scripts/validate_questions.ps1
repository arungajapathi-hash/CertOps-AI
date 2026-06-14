# Validate the Foundry-grounded, cached question-bank flow end to end.
# Usage:  .\scripts\validate_questions.ps1            # defaults to AZ-204
#         .\scripts\validate_questions.ps1 AZ-900
#         .\scripts\validate_questions.ps1 AWS-SAA L-5005

param(
    [string]$Cert = "AZ-204",
    [string]$LearnerId = "L-9100",
    [string]$ApiBase = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$bankPath = Join-Path $PSScriptRoot "..\data\question_banks\$($Cert.ToLower()).json"

function Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    PASS  $msg" -ForegroundColor Green }
function Bad($msg)  { Write-Host "    FAIL  $msg" -ForegroundColor Red }

# 1. Backend reachable
Step 1 "Checking backend health at $ApiBase ..."
try {
    $h = Invoke-RestMethod "$ApiBase/health" -TimeoutSec 10
    Ok "backend online (status=$($h.status))"
} catch {
    Bad "backend unreachable - start it:  uvicorn backend.main:app --port 8000"
    exit 1
}

# 2. Note whether a cache already exists (first run will be slow, cached run fast)
Step 2 "Cache state before run"
$preExisted = Test-Path $bankPath
if ($preExisted) { Write-Host "    cache already exists -> expect a FAST run" -ForegroundColor Yellow }
else             { Write-Host "    no cache -> first run builds the bank (may take 1-4 min)" -ForegroundColor Yellow }

# 3. Run the pipeline (this generates+caches on first encounter)
Step 3 "Running pipeline for $Cert ..."
$body = @{ learner_id = $LearnerId; role = "Cloud Engineer"; certification = $Cert; target_weeks = 6 } | ConvertTo-Json
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$res = Invoke-RestMethod "$ApiBase/pipeline" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 400
$sw.Stop()
$questions = $res.phases.assessment.questions
Write-Host "    pipeline returned in $([math]::Round($sw.Elapsed.TotalSeconds,1))s, status=$($res.status)"

# 4. Question count + uniqueness (the original complaint: repeated/static questions)
Step 4 "Validating questions"
$total = $questions.Count
$uniqueStems = ($questions | Select-Object -ExpandProperty question | Sort-Object -Unique).Count
$uniqueAns   = ($questions | ForEach-Object { ($_.options.PSObject.Properties.Name | Sort-Object) -join '' } | Sort-Object -Unique).Count
Write-Host "    total questions : $total"
Write-Host "    unique stems    : $uniqueStems"
if ($total -gt 0 -and $uniqueStems -eq $total) { Ok "no repeated questions within the exam" }
else { Bad "repetition detected ($uniqueStems unique of $total)" }

# 5. Foundry grounding metadata
Step 5 "Checking Foundry IQ grounding"
$grounded = ($questions | Where-Object { $_.grounded_in } | Measure-Object).Count
$withSource = ($questions | Where-Object { $_.source } | Measure-Object).Count
Write-Host "    grounded_in set : $grounded/$total"
Write-Host "    source cited    : $withSource/$total"
if ($grounded -gt 0) { Ok "questions carry grounding metadata (grounded_in='$($questions[0].grounded_in)')" }
else { Write-Host "    NOTE  grounded_in absent - served from a pre-existing static bank" -ForegroundColor Yellow }

# 6. No cache by design — confirm nothing is persisted to disk.
Step 6 "Confirming no disk cache is written (built fresh from Foundry IQ each time)"
if (Test-Path $bankPath) { Bad "unexpected cache file at $bankPath (should not persist)" }
else { Ok "no persisted bank - questions are built per exam" }

# 7. Second run (fresh learner) should REGENERATE different questions.
#    Use a DIFFERENT learner id - the first learner is parked at
#    'awaiting_assessment', so the concurrency guard would (correctly) 409 it.
Step 7 "Re-running with a fresh learner to confirm questions are regenerated"
$body2 = @{ learner_id = "$($LearnerId)-b"; role = "Cloud Engineer"; certification = $Cert; target_weeks = 6 } | ConvertTo-Json
$sw2 = [System.Diagnostics.Stopwatch]::StartNew()
$res2 = Invoke-RestMethod "$ApiBase/pipeline" -Method Post -Body $body2 -ContentType "application/json" -TimeoutSec 400
$sw2.Stop()
$q2 = $res2.phases.assessment.questions
$stems1 = $questions | Select-Object -ExpandProperty question
$stems2 = $q2 | Select-Object -ExpandProperty question
$overlap = ($stems1 | Where-Object { $stems2 -contains $_ }).Count
Write-Host "    run1=$($stems1.Count) run2=$($stems2.Count) questions, identical stems shared=$overlap"
if ($overlap -lt $stems1.Count) { Ok "second exam is freshly generated (not a repeat of run 1)" }
else { Bad "both runs returned the same questions" }

# 8. Sample preview
Step 8 "Sample questions"
$questions | Select-Object -First 3 | ForEach-Object {
    Write-Host "    - [$($_.topic)] $($_.question.Substring(0,[Math]::Min(80,$_.question.Length)))..." -ForegroundColor Gray
}

Write-Host "`nValidation complete.`n" -ForegroundColor Cyan
