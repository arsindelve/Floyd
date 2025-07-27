# Script to force update Lambda deployment

# Clean build artifacts
Write-Host "Cleaning build artifacts..."
if (Test-Path -Path ".aws-sam") { Remove-Item -Recurse -Force ".aws-sam" }
if (Test-Path -Path "build") { Remove-Item -Recurse -Force "build" }

# Build the application
Write-Host "Building the application..."
sam build

# Deploy with force-upload flag to ensure code changes are pushed
Write-Host "Deploying with force-upload..."
sam deploy --force-upload --no-fail-on-empty-changeset

Write-Host "Deployment completed"
