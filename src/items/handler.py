import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from common.response import success, error
from common.validators import validate_item

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["ITEMS_TABLE"]
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path = event.get("path", "")
    path_params = event.get("pathParameters") or {}

    try:
        if method == "GET" and "itemId" not in path_params:
            return list_items()

        if method == "POST":
            body = json.loads(event.get("body") or "{}")
            return create_item(body)

        if method == "PUT" and "itemId" in path_params:
            body = json.loads(event.get("body") or "{}")
            return update_item(path_params["itemId"], body)

        return error(404, "Route not found")

    except json.JSONDecodeError:
        return error(400, "Invalid JSON body")
    except Exception as e:
        print(f"Unhandled error: {e}")
        return error(500, "Internal server error")


def list_items():
    result = table.scan()
    items = result.get("Items", [])
    return success(200, {"items": items, "count": len(items)})


def create_item(body):
    validation_error = validate_item(body)
    if validation_error:
        return error(400, validation_error)

    item = {
        "itemId":      str(uuid.uuid4()),
        "name":        body["name"],
        "sku":         body.get("sku", "").upper(),
        "quantity":    int(body.get("quantity", 0)),
        "price":       float(body.get("price", 0.0)),
        "category":    body.get("category", "general"),
        "status":      "active",
        "createdAt":   datetime.now(timezone.utc).isoformat(),
        "updatedAt":   datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=item)
    return success(201, {"message": "Item created", "item": item})


def update_item(item_id, body):
    existing = table.get_item(Key={"itemId": item_id}).get("Item")
    if not existing:
        return error(404, f"Item {item_id} not found")

    update_expr = "SET updatedAt = :updatedAt"
    expr_values = {":updatedAt": datetime.now(timezone.utc).isoformat()}

    allowed_fields = ["name", "quantity", "price", "category", "status", "sku"]
    for field in allowed_fields:
        if field in body:
            update_expr += f", {field} = :{field}"
            expr_values[f":{field}"] = body[field]

    result = table.update_item(
        Key={"itemId": item_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ReturnValues="ALL_NEW"
    )

    return success(200, {"message": "Item updated", "item": result["Attributes"]})
