output "api_endpoint" {
  description = "Base URL of the deployed API"
  value       = "https://${aws_api_gateway_rest_api.erp_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "items_table_name" {
  description = "DynamoDB items table name"
  value       = aws_dynamodb_table.items.name
}

output "orders_table_name" {
  description = "DynamoDB orders table name"
  value       = aws_dynamodb_table.orders.name
}

output "items_lambda_name" {
  description = "Items Lambda function name"
  value       = aws_lambda_function.items.function_name
}

output "orders_lambda_name" {
  description = "Orders Lambda function name"
  value       = aws_lambda_function.orders.function_name
}
