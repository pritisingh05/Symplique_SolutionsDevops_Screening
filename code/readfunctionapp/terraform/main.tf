provider "azurerm" {
  features {}
}

data "azurerm_resource_group" "existing" {
  name = "example-resources"
}

data "azurerm_storage_account" "existing" {
  name                = "archive-cold-sa"
  resource_group_name = data.azurerm_resource_group.existing.name
  location            = data.azurerm_resource_group.existing.location

}

data "azurerm_storage_container" "existing" {
  name                  = "archive-cold-storage-container"
  storage_account_name  = data.azurerm_storage_account.existing.name
}

resource "azurerm_app_service_plan" "example" {
  name                = "read-app-service-plan"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
  kind                = "FunctionApp"
  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}

resource "azurerm_linux_function_app" "example" {
  name                = "readfunctionapp"
  resource_group_name = data.azurerm_resource_group.existing.name
  location            = data.azurerm_resource_group.existing.location

  storage_account_name       = data.azurerm_storage_account.existing.name
  storage_account_access_key = data.azurerm_storage_account.existing.primary_access_key
  service_plan_id            = data.azurerm_app_service_plan.example.id

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
    BLOB_CONN_STRING          = data.azurerm_storage_account.existing.primary_connection_string
    BLOB_CONTAINER_NAME       = data.azurerm_storage_container.existing.name
  }
}
