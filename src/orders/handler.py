import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from common.response import success, error
from common.validators import validate_order

dynamodb = boto3.resource("dynamodb")
ORDERS_TABLE = os.environ["ORDERS_TABLE"]
ITEMS_TABLE  = os.environ["ITEMS_TABLE"]
orders_table = dynamodb.Table(ORDERS_TABLE)
items_table  = dynamodb.Table(ITEMS_TABLE)


def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    path_params = event.get("pathParameters") or {}

    try:
        if method == "POST":
            body = json.loads(event.get("body") or "{}")
            return create_order(body)

        if method == "GET" and "orderId" in path_params:
            return get_order(path_params["orderId"])

        return error(404, "Route not found")

    except json.JSONDecodeError:
        return error(400, "Invalid JSON body")
    except Exception as e:
        print(f"Unhandled error: {e}")
        return error(500, "Internal server error")


def create_order(body):
    validation_error = validate_order(body)
    if validation_error:
        return error(400, validation_error)

    line_items = body.get("lineItems", [])
    enriched_lines = []
    total_amount = 0.0

    for line in line_items:
        item_id  = line.get("itemId")
        quantity = int(line.get("quantity", 1))

        db_item = items_table.get_item(Key={"itemId": item_id}).get("Item")
        if not db_item:
            return error(404, f"Item {item_id} not found in inventory")

        if db_item.get("status") != "active":
            return error(400, f"Item {item_id} is not available for ordering")

        if int(db_item.get("quantity", 0)) < quantity:
            return error(400, f"Insufficient stock for item {item_id}. Available: {db_item['quantity']}")

        line_total = float(db_item["price"]) * quantity
        total_amount += line_total

        enriched_lines.append({
            "itemId":    item_id,
            "name":      db_item["name"],
            "sku":       db_item.get("sku", ""),
            "quantity":  quantity,
            "unitPrice": float(db_item["price"]),
            "lineTotal": round(line_total, 2),
        })

        # Deduct stock
        items_table.update_item(
            Key={"itemId": item_id},
            UpdateExpression="SET quantity = quantity - :qty, updatedAt = :ts",
            ExpressionAttributeValues={
                ":qty": quantity,
                ":ts":  datetime.now(timezone.utc).isoformat()
            }
        )

    order = {
        "orderId":     str(uuid.uuid4()),
        "customerId":  body.get("customerId", "guest"),
        "lineItems":   enriched_lines,
        "totalAmount": round(total_amount, 2),
        "status":      "confirmed",
        "notes":       body.get("notes", ""),
        "createdAt":   datetime.now(timezone.utc).isoformat(),
        "updatedAt":   datetime.now(timezone.utc).isoformat(),
    }

    orders_table.put_item(Item=order)
    return success(201, {"message": "Order created", "order": order})


def get_order(order_id):
    result = orders_table.get_item(Key={"orderId": order_id})
    order  = result.get("Item")
    if not order:
        return error(404, f"Order {order_id} not found")
    return success(200, {"order": order})
