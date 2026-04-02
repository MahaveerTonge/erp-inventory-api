def validate_item(body: dict) -> str | None:
    if not body.get("name"):
        return "Field 'name' is required"
    if len(body["name"]) < 2:
        return "Field 'name' must be at least 2 characters"
    if "price" in body:
        try:
            if float(body["price"]) < 0:
                return "Field 'price' must be non-negative"
        except (ValueError, TypeError):
            return "Field 'price' must be a number"
    if "quantity" in body:
        try:
            if int(body["quantity"]) < 0:
                return "Field 'quantity' must be non-negative"
        except (ValueError, TypeError):
            return "Field 'quantity' must be an integer"
    return None


def validate_order(body: dict) -> str | None:
    line_items = body.get("lineItems")
    if not line_items or not isinstance(line_items, list):
        return "Field 'lineItems' is required and must be a non-empty list"
    for i, line in enumerate(line_items):
        if not line.get("itemId"):
            return f"lineItems[{i}]: 'itemId' is required"
        if not line.get("quantity") or int(line["quantity"]) < 1:
            return f"lineItems[{i}]: 'quantity' must be at least 1"
    return None
