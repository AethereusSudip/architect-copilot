# Terraform starter for ADR-001 (modular monolith on managed PaaS), target cloud: Azure.
# Candidate services from the ADR: App Service, Azure SQL, Blob Storage, Key Vault, Application Insights.
# REVIEW: validate SKUs, regions and service choices against the approved catalogue before use.

terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "subscription_id" { type = string }
variable "prefix" {
  type    = string
  default = "licportal"
}
variable "environment" { type = string }
variable "location" {
  type        = string
  description = "ADR NFR: data must stay in the United States."
  validation {
    condition     = contains(["eastus", "eastus2", "centralus", "westus2", "westus3", "southcentralus"], var.location)
    error_message = "Location must be a US region (data residency)."
  }
}
variable "app_sku" {
  type    = string
  default = "P1v3" # ASSUMPTION: sized for under 500 concurrent users; scale out during the filing window
}

locals {
  name = "${var.prefix}-${var.environment}"
  tags = { workload = "licensing-portal", adr = "ADR-001", generated = "ai-draft" }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.name}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  retention_in_days   = 90 # REVIEW: retention period is an open question in the ADR
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${local.name}"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
}

resource "azurerm_mssql_server" "main" {
  name                         = "sql-${local.name}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = "sqladmin"
  administrator_login_password = "P@ssw0rd123!"
  minimum_tls_version          = "1.2"
}

resource "azurerm_mssql_database" "main" {
  name      = "sqldb-${local.name}"
  server_id = azurerm_mssql_server.main.id
  sku_name  = "S2" # ASSUMPTION: moderate load; review after load test of the filing window
}

resource "azurerm_storage_account" "documents" {
  name                            = "st${var.prefix}${var.environment}docs"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS" # REVIEW: RTO/RPO unknown; GRS may be required
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
}

resource "azurerm_storage_container" "documents" {
  name                  = "application-documents"
  storage_account_id    = azurerm_storage_account.documents.id
  container_access_type = "private"
}

resource "azurerm_service_plan" "main" {
  name                = "asp-${local.name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.app_sku
}

resource "azurerm_linux_web_app" "portal" {
  name                = "app-${local.name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true

  site_config {
    minimum_tls_version = "1.2"
    application_stack { python_version = "3.12" } # ASSUMPTION: stack per scaffold
  }

  app_settings = {
    APP_ENV                               = var.environment
    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.main.connection_string
    DOCUMENT_CONTAINER                    = azurerm_storage_container.documents.name
  }
}

# REVIEW: nightly finance / student data jobs (Azure Functions timer triggers) and the
# payment provider egress rules are not yet included in this starter.
