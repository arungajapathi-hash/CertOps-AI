# Diagnose the Azure AI Foundry IQ connection end to end.
# Usage:  .\scripts\test_foundry.ps1            # tests AZ-204
#         .\scripts\test_foundry.ps1 AZ-900
#
# Walks through: env vars -> credential source -> client construct ->
# agent resolve -> live retrieval, and tells you exactly where it breaks.

param([string]$Cert = "AZ-204")

$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

function Head($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  PASS  $m" -ForegroundColor Green }
function Bad($m)  { Write-Host "  FAIL  $m" -ForegroundColor Red }
function Info($m) { Write-Host "  ..    $m" -ForegroundColor Gray }

# 1. Required env vars present
Head "1. Environment variables"
$envCheck = @"
import os
from dotenv import load_dotenv
load_dotenv('.env')
keys = ['AZURE_OPENAI_ENDPOINT','AZURE_OPENAI_DEPLOYMENT','USE_FOUNDRY_IQ']
for k in keys:
    print(f'{k}={os.getenv(k)}')
sp = all(os.getenv(x) for x in ['AZURE_CLIENT_ID','AZURE_CLIENT_SECRET','AZURE_TENANT_ID'])
print('SERVICE_PRINCIPAL_SET=' + str(sp))
"@
$envOut = python -c $envCheck 2>&1
$envOut | ForEach-Object { Info $_ }
if ($envOut -match "AZURE_OPENAI_ENDPOINT=https://") { Ok "AZURE_OPENAI_ENDPOINT looks valid" }
else { Bad "AZURE_OPENAI_ENDPOINT missing or malformed" }
if ($envOut -match "AZURE_OPENAI_DEPLOYMENT=\w") { Ok "Agent deployment name set" }
else { Bad "AZURE_OPENAI_DEPLOYMENT (agent name) missing" }

# 2. Which credential will DefaultAzureCredential use?
Head "2. Credential source"
$spSet = ($envOut -match "SERVICE_PRINCIPAL_SET=True").Count -gt 0
if ($spSet) {
    Ok "Service principal env vars set -> no az login needed"
} else {
    Info "No service principal vars; checking az login..."
    $acct = az account show --query "user.name" -o tsv 2>$null
    if ($LASTEXITCODE -eq 0 -and $acct) { Ok "az login active as: $acct" }
    else { Bad "No credential available -> run 'az login' OR set AZURE_CLIENT_ID/SECRET/TENANT_ID" }
}

# 3. Live connection + retrieval through the plugin
Head "3. Live Foundry IQ retrieval ($Cert)"
$pyTest = @"
from dotenv import load_dotenv; load_dotenv('.env')
from backend.plugins.foundry_knowledge_plugin import FoundryKnowledgePlugin
p = FoundryKnowledgePlugin()
print('CLIENT_CONSTRUCTED=' + str(p.foundry_client is not None))
g = p.get_certification_guide('$Cert')
print('SOURCE=' + str(g.get('source')))
print('LEN=' + str(len(g.get('content',''))))
print('PREVIEW=' + g.get('content','')[:140].replace(chr(10),' '))
"@
$out = python -c $pyTest 2>&1
$out | ForEach-Object { Info $_ }

$source = ($out | Select-String "^SOURCE=").ToString() -replace "SOURCE=",""
Head "Verdict"
if ($source -match "Foundry IQ") {
    Ok "Connected to Foundry IQ - questions will be grounded in your knowledge base"
} elseif ($source -match "Dynamic Web|LLM Knowledge") {
    Bad "Fell back to '$source' - Foundry IQ not reachable"
    Write-Host "  Likely cause (read the [FoundryIQ] line above):" -ForegroundColor Yellow
    Write-Host "   - 'Please run az login'      -> no credential (step 2)" -ForegroundColor Yellow
    Write-Host "   - 403 / authorization        -> missing RBAC role" -ForegroundColor Yellow
    Write-Host "       (Azure AI User + Cognitive Services OpenAI User)" -ForegroundColor Yellow
    Write-Host "   - model/deployment not found -> AZURE_OPENAI_DEPLOYMENT wrong" -ForegroundColor Yellow
} else {
    Bad "Unexpected source: '$source'"
}
Write-Host ""
