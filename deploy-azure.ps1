# Azure Container Apps Deployment Script for PowerShell
# Make sure you have Azure CLI installed and logged in

# Configuration
$RESOURCE_GROUP = "ai-job-finder-rg"
$LOCATION = "eastus"
$CONTAINER_APP_ENV = "ai-job-finder-env"
$CONTAINER_APP_NAME = "ai-job-finder-app"
$ACR_NAME = "aijobfinderacr$(Get-Date -Format 'yyyyMMddHHmmss')"
$IMAGE_NAME = "ai-job-finder"

Write-Host "🚀 Starting Azure Container Apps deployment..." -ForegroundColor Green

# Create resource group
Write-Host "📦 Creating resource group..." -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
Write-Host "🏗️ Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR login server
$ACR_LOGIN_SERVER = az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "loginServer" --output tsv

# Build and push Docker image
Write-Host "🐳 Building and pushing Docker image..." -ForegroundColor Yellow
az acr build --registry $ACR_NAME --image "${IMAGE_NAME}:latest" .

# Create Container Apps environment
Write-Host "🌍 Creating Container Apps environment..." -ForegroundColor Yellow
az containerapp env create --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP --location $LOCATION

# Create the container app
Write-Host "📱 Creating container app..." -ForegroundColor Yellow
az containerapp create `
  --name $CONTAINER_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --environment $CONTAINER_APP_ENV `
  --image "$ACR_LOGIN_SERVER/${IMAGE_NAME}:latest" `
  --target-port 8080 `
  --ingress 'external' `
  --registry-server $ACR_LOGIN_SERVER `
  --cpu 0.5 `
  --memory 1Gi `
  --min-replicas 1 `
  --max-replicas 3 `
  --env-vars FLASK_ENV=production

Write-Host "✅ Deployment completed!" -ForegroundColor Green
Write-Host "🌐 Your app will be available at:" -ForegroundColor Cyan
$APP_URL = az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" --output tsv
Write-Host "https://$APP_URL" -ForegroundColor Blue

Write-Host ""
Write-Host "🔑 Next steps:" -ForegroundColor Yellow
Write-Host "1. Set environment variables (API keys) using:" -ForegroundColor White
Write-Host "   az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --set-env-vars GOOGLE_API_KEY='your-key' RAPIDAPI_KEY='your-key'" -ForegroundColor Gray
Write-Host "2. Monitor logs using:" -ForegroundColor White
Write-Host "   az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow" -ForegroundColor Gray