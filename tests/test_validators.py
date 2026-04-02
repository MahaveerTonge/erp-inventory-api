import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from common.validators import validate_item, validate_order


def test_validate_item_valid():
    assert validate_item({"name": "Widget", "price": 9.99, "quantity": 10}) is None


def test_validate_item_missing_name():
    result = validate_item({"price": 5.0})
    assert result is not None
    assert "name" in result


def test_validate_item_short_name():
    result = validate_item({"name": "X"})
    assert result is not None


def test_validate_item_negative_price():
    result = validate_item({"name": "Widget", "price": -1.0})
    assert result is not None
    assert "price" in result


def test_validate_item_negative_quantity():
    result = validate_item({"name": "Widget", "quantity": -5})
    assert result is not None
    assert "quantity" in result


def test_validate_order_valid():
    assert validate_order({
        "lineItems": [{"itemId": "item-123", "quantity": 2}]
    }) is None


def test_validate_order_missing_line_items():
    result = validate_order({"customerId": "cust-001"})
    assert result is not None


def test_validate_order_empty_line_items():
    result = validate_order({"lineItems": []})
    assert result is not None


def test_validate_order_missing_item_id():
    result = validate_order({"lineItems": [{"quantity": 1}]})
    assert result is not None
    assert "itemId" in result


def test_validate_order_zero_quantity():
    result = validate_order({"lineItems": [{"itemId": "abc", "quantity": 0}]})
    assert result is not None
    assert "quantity" in result
