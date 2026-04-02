import json
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/items"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

os.environ["ITEMS_TABLE"]  = "test-items"
os.environ["ORDERS_TABLE"] = "test-orders"
os.environ["ENVIRONMENT"]  = "test"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


def make_event(method, path="/items", body=None, path_params=None):
    return {
        "httpMethod":     method,
        "path":           path,
        "pathParameters": path_params,
        "body":           json.dumps(body) if body else None,
    }


@patch("items.handler.table")
def test_create_item_success(mock_table):
    mock_table.put_item = MagicMock()
    from items.handler import lambda_handler

    event = make_event("POST", body={
        "name": "Widget A", "sku": "WGT-001",
        "price": 9.99, "quantity": 100, "category": "widgets"
    })
    response = lambda_handler(event, {})
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["item"]["name"] == "Widget A"
    assert body["item"]["sku"] == "WGT-001"


@patch("items.handler.table")
def test_create_item_missing_name(mock_table):
    from items.handler import lambda_handler

    event = make_event("POST", body={"price": 5.00})
    response = lambda_handler(event, {})
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "name" in body["error"]


@patch("items.handler.table")
def test_create_item_negative_price(mock_table):
    from items.handler import lambda_handler

    event = make_event("POST", body={"name": "Bad Item", "price": -1.0})
    response = lambda_handler(event, {})
    assert response["statusCode"] == 400


@patch("items.handler.table")
def test_list_items(mock_table):
    mock_table.scan.return_value = {"Items": [
        {"itemId": "abc", "name": "Widget A", "quantity": 10}
    ]}
    from items.handler import lambda_handler

    event = make_event("GET")
    response = lambda_handler(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 1


@patch("items.handler.table")
def test_update_item_not_found(mock_table):
    mock_table.get_item.return_value = {}
    from items.handler import lambda_handler

    event = make_event("PUT", path="/items/nonexistent",
                       body={"quantity": 50},
                       path_params={"itemId": "nonexistent"})
    response = lambda_handler(event, {})
    assert response["statusCode"] == 404


@patch("items.handler.table")
def test_unknown_route(mock_table):
    from items.handler import lambda_handler

    event = make_event("DELETE")
    response = lambda_handler(event, {})
    assert response["statusCode"] == 404
