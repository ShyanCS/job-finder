#!/bin/bash

# Azure Container Apps Deployment Script
# Make sure you have Azure CLI installed and logged in

set -e

# Configuration
RESOURCE_GROUP="ai-job-finder-rg"
LOCATION="eastus"
CONTAINER_APP_ENV="ai-job-finder-env"
CONTAINER_APP_NAME="ai-job-finder-app"
ACR_NAME="aijobfinderacr$(date +%s)"
IMAGE_NAME="ai-job-finder"

echo "🚀 Starting Azure Container Apps deployment..."

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "🏗️ Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "loginServer" --output tsv)

# Build and push Docker image
echo "🐳 Building and pushing Docker image..."
az acr build --registry $ACR_NAME --image $IMAGE_NAME:latest .

# Create Container Apps environment
echo "🌍 Creating Container Apps environment..."
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create the container app
echo "📱 Creating container app..."
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_LOGIN_SERVER/$IMAGE_NAME:latest \
  --target-port 8080 \
  --ingress 'external' \
  --registry-server $ACR_LOGIN_SERVER \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars FLASK_ENV=production

echo "✅ Deployment completed!"
echo "🌐 Your app will be available at:"
az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" --output tsv

echo ""
echo "🔑 Next steps:"
echo "1. Set environment variables (API keys) using:"
echo "   az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --set-env-vars GOOGLE_API_KEY='your-key' RAPIDAPI_KEY='your-key'"
echo "2. Monitor logs using:"
echo "   az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"