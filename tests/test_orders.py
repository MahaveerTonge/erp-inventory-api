import json
import sys
import os
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/orders"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

os.environ["ITEMS_TABLE"]  = "test-items"
os.environ["ORDERS_TABLE"] = "test-orders"
os.environ["ENVIRONMENT"]  = "test"


def make_event(method, path="/orders", body=None, path_params=None):
    return {
        "httpMethod":     method,
        "path":           path,
        "pathParameters": path_params,
        "body":           json.dumps(body) if body else None,
    }


@patch("handler.orders_table")
@patch("handler.items_table")
def test_create_order_success(mock_items, mock_orders):
    mock_items.get_item.return_value = {"Item": {
        "itemId": "item-123", "name": "Widget A", "sku": "WGT-001",
        "price": Decimal("9.99"), "quantity": Decimal("50"), "status": "active"
    }}
    mock_items.update_item = MagicMock()
    mock_orders.put_item   = MagicMock()

    from handler import lambda_handler
    event = make_event("POST", body={
        "customerId": "cust-001",
        "lineItems": [{"itemId": "item-123", "quantity": 2}]
    })
    response = lambda_handler(event, {})
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["order"]["status"] == "confirmed"
    assert body["order"]["totalAmount"] == 19.98


@patch("handler.orders_table")
@patch("handler.items_table")
def test_create_order_item_not_found(mock_items, mock_orders):
    mock_items.get_item.return_value = {}
    from handler import lambda_handler

    event = make_event("POST", body={
        "lineItems": [{"itemId": "nonexistent", "quantity": 1}]
    })
    response = lambda_handler(event, {})
    assert response["statusCode"] == 404


@patch("handler.orders_table")
@patch("handler.items_table")
def test_create_order_insufficient_stock(mock_items, mock_orders):
    mock_items.get_item.return_value = {"Item": {
        "itemId": "item-123", "name": "Widget", "price": Decimal("5.00"),
        "quantity": Decimal("1"), "status": "active"
    }}
    from handler import lambda_handler

    event = make_event("POST", body={
        "lineItems": [{"itemId": "item-123", "quantity": 99}]
    })
    response = lambda_handler(event, {})
    assert response["statusCode"] == 400
    assert "Insufficient" in json.loads(response["body"])["error"]


@patch("handler.orders_table")
@patch("handler.items_table")
def test_create_order_missing_line_items(mock_items, mock_orders):
    from handler import lambda_handler

    event = make_event("POST", body={"customerId": "cust-001"})
    response = lambda_handler(event, {})
    assert response["statusCode"] == 400


@patch("handler.orders_table")
@patch("handler.items_table")
def test_get_order_not_found(mock_items, mock_orders):
    mock_orders.get_item.return_value = {}
    from handler import lambda_handler

    event = make_event("GET", path="/orders/fake-id",
                       path_params={"orderId": "fake-id"})
    response = lambda_handler(event, {})
    assert response["statusCode"] == 404
