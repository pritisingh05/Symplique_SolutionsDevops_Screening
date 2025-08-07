provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "example" {
  name     = "example-resources"
  location = "example-location"
}

resource "azurerm_storage_account" "example" {
  name                     = "archive-cold-sa"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "example" {
  name                  = "archive-cold-storage-container"
  storage_account_name  = azurerm_storage_account.example.name
  container_access_type = "private"
}

resource "azurerm_app_service_plan" "example" {
  name                = "archive-app-service-plan"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
  kind                = "FunctionApp"
  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}

resource "azurerm_linux_function_app" "example" {
  name                = "archivefunctionapp"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location

  storage_account_name       = azurerm_storage_account.example.name
  storage_account_access_key = azurerm_storage_account.example.primary_access_key
  service_plan_id            = azurerm_app_service_plan.example.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME  = "python"
    COSMOS_ENDPOINT           = "<your-cosmos-endpoint>"
    COSMOS_KEY                = "<your-cosmos-key>"
    COSMOS_DB_NAME            = "<your-cosmos-db-name>"
    COSMOS_CONTAINER_NAME     = "<your-cosmos-container-name>"
    BLOB_CONN_STRING          = azurerm_storage_account.example.primary_connection_string
    BLOB_CONTAINER_NAME       = azurerm_storage_container.example.name
  }
}