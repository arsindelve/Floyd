# Script to test both Lambda endpoints using JSON files

# Set Lambda function ARN - we only have one function
$functionName = "arn:aws:lambda:us-east-1:576431164672:function:Floyd-LangGraphFunction-GefcykaLqwp-MySimpleLambda-lBRzg1jLKvXP"
Write-Host "Using Lambda function: $functionName"

# Test with event.json (main router endpoint)
Write-Host "\nTesting with event.json (router endpoint)..." -ForegroundColor Cyan
$eventJson = Get-Content -Raw -Path event.json
# Convert to base64 for AWS CLI
$eventJsonBytes = [System.Text.Encoding]::UTF8.GetBytes($eventJson)
$eventJsonBase64 = [Convert]::ToBase64String($eventJsonBytes)
aws lambda invoke --function-name $functionName --payload $eventJsonBase64 --cli-binary-format base64 response_router.json
Write-Host "Response saved to response_router.json"
Get-Content -Path response_router.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Test with rewrite_event.json (rewrite endpoint)
Write-Host "\nTesting with rewrite_event.json (RewriteSecondPerson endpoint)..." -ForegroundColor Cyan
# Read the existing JSON content
$rewriteContent = Get-Content -Raw -Path rewrite_event.json | ConvertFrom-Json
# Add the assistant type for RewriteSecondPerson
$rewriteContent | Add-Member -MemberType NoteProperty -Name "assistant" -Value "RewriteSecondPerson" -Force
# Convert back to JSON string
$rewriteEventJson = $rewriteContent | ConvertTo-Json -Compress
Write-Host "Modified payload: $rewriteEventJson"
# Convert to base64 for AWS CLI
$rewriteEventJsonBytes = [System.Text.Encoding]::UTF8.GetBytes($rewriteEventJson)
$rewriteEventJsonBase64 = [Convert]::ToBase64String($rewriteEventJsonBytes)
aws lambda invoke --function-name $functionName --payload $rewriteEventJsonBase64 --cli-binary-format base64 response_rewrite.json
Write-Host "Response saved to response_rewrite.json"
Get-Content -Path response_rewrite.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
