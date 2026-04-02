terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "erp-inventory-tfstate"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_dynamodb_table" "items" {
  name         = "${var.project_name}-items-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "itemId"
  attribute {
    name = "itemId"
    type = "S"
  }
  tags = { Project = var.project_name, Environment = var.environment }
}

resource "aws_dynamodb_table" "orders" {
  name         = "${var.project_name}-orders-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "orderId"
  attribute {
    name = "orderId"
    type = "S"
  }
  tags = { Project = var.project_name, Environment = var.environment }
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${var.project_name}-lambda-dynamodb-policy"
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["dynamodb:GetItem","dynamodb:PutItem","dynamodb:UpdateItem",
                  "dynamodb:DeleteItem","dynamodb:Scan","dynamodb:Query"]
        Resource = [aws_dynamodb_table.items.arn, aws_dynamodb_table.orders.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "archive_file" "items_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/items"
  output_path = "${path.module}/zips/items.zip"
}

data "archive_file" "orders_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/orders"
  output_path = "${path.module}/zips/orders.zip"
}

resource "aws_lambda_function" "items" {
  filename         = data.archive_file.items_zip.output_path
  function_name    = "${var.project_name}-items-${var.environment}"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.items_zip.output_base64sha256
  timeout          = 30
  environment {
    variables = {
      ITEMS_TABLE  = aws_dynamodb_table.items.name
      ORDERS_TABLE = aws_dynamodb_table.orders.name
      ENVIRONMENT  = var.environment
    }
  }
}

resource "aws_lambda_function" "orders" {
  filename         = data.archive_file.orders_zip.output_path
  function_name    = "${var.project_name}-orders-${var.environment}"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.orders_zip.output_base64sha256
  timeout          = 30
  environment {
    variables = {
      ITEMS_TABLE  = aws_dynamodb_table.items.name
      ORDERS_TABLE = aws_dynamodb_table.orders.name
      ENVIRONMENT  = var.environment
    }
  }
}

resource "aws_cloudwatch_log_group" "items_logs" {
  name              = "/aws/lambda/${aws_lambda_function.items.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "orders_logs" {
  name              = "/aws/lambda/${aws_lambda_function.orders.function_name}"
  retention_in_days = 14
}

resource "aws_api_gateway_rest_api" "erp_api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "ERP Inventory & Order Management API"
}

resource "aws_api_gateway_resource" "items" {
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  parent_id   = aws_api_gateway_rest_api.erp_api.root_resource_id
  path_part   = "items"
}

resource "aws_api_gateway_resource" "item_id" {
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  parent_id   = aws_api_gateway_resource.items.id
  path_part   = "{itemId}"
}

resource "aws_api_gateway_resource" "orders" {
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  parent_id   = aws_api_gateway_rest_api.erp_api.root_resource_id
  path_part   = "orders"
}

resource "aws_api_gateway_resource" "order_id" {
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  parent_id   = aws_api_gateway_resource.orders.id
  path_part   = "{orderId}"
}

data "aws_caller_identity" "current" {}

module "items_get" {
  source      = "./modules/api_method"
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  resource_id = aws_api_gateway_resource.items.id
  http_method = "GET"
  lambda_arn  = aws_lambda_function.items.arn
  lambda_name = aws_lambda_function.items.function_name
  aws_region  = var.aws_region
  account_id  = data.aws_caller_identity.current.account_id
}

module "items_post" {
  source      = "./modules/api_method"
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  resource_id = aws_api_gateway_resource.items.id
  http_method = "POST"
  lambda_arn  = aws_lambda_function.items.arn
  lambda_name = aws_lambda_function.items.function_name
  aws_region  = var.aws_region
  account_id  = data.aws_caller_identity.current.account_id
}

module "item_put" {
  source      = "./modules/api_method"
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  resource_id = aws_api_gateway_resource.item_id.id
  http_method = "PUT"
  lambda_arn  = aws_lambda_function.items.arn
  lambda_name = aws_lambda_function.items.function_name
  aws_region  = var.aws_region
  account_id  = data.aws_caller_identity.current.account_id
}

module "orders_post" {
  source      = "./modules/api_method"
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  resource_id = aws_api_gateway_resource.orders.id
  http_method = "POST"
  lambda_arn  = aws_lambda_function.orders.arn
  lambda_name = aws_lambda_function.orders.function_name
  aws_region  = var.aws_region
  account_id  = data.aws_caller_identity.current.account_id
}

module "order_get" {
  source      = "./modules/api_method"
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  resource_id = aws_api_gateway_resource.order_id.id
  http_method = "GET"
  lambda_arn  = aws_lambda_function.orders.arn
  lambda_name = aws_lambda_function.orders.function_name
  aws_region  = var.aws_region
  account_id  = data.aws_caller_identity.current.account_id
}

resource "aws_api_gateway_deployment" "erp_api" {
  rest_api_id = aws_api_gateway_rest_api.erp_api.id
  depends_on = [
    module.items_get, module.items_post, module.item_put,
    module.orders_post, module.order_get
  ]
  lifecycle { create_before_destroy = true }
}

resource "aws_api_gateway_stage" "erp_api" {
  deployment_id = aws_api_gateway_deployment.erp_api.id
  rest_api_id   = aws_api_gateway_rest_api.erp_api.id
  stage_name    = var.environment
}
