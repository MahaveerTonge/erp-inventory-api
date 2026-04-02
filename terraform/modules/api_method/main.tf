variable "rest_api_id" { type = string }
variable "resource_id" { type = string }
variable "http_method" { type = string }
variable "lambda_arn"  { type = string }
variable "lambda_name" { type = string }
variable "aws_region"  { type = string }
variable "account_id"  { type = string }

resource "aws_api_gateway_method" "method" {
  rest_api_id   = var.rest_api_id
  resource_id   = var.resource_id
  http_method   = var.http_method
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "integration" {
  rest_api_id             = var.rest_api_id
  resource_id             = var.resource_id
  http_method             = aws_api_gateway_method.method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${var.lambda_arn}/invocations"
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGateway-${var.http_method}-${var.resource_id}"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${var.aws_region}:${var.account_id}:${var.rest_api_id}/*/*"
}
