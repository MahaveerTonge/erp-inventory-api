# ERP Inventory & Order Management API

A production-grade serverless REST API for inventory and order management, deployed via a fully automated CI/CD pipeline.

## Architecture

```
GitHub Push → GitHub Actions → Tests → Terraform → AWS API Gateway → Lambda (Python) → DynamoDB
```

**Stack:** Python 3.11 · AWS Lambda · API Gateway · DynamoDB · Terraform · GitHub Actions · CloudWatch

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /items | List all inventory items |
| POST | /items | Create a new item |
| PUT | /items/{itemId} | Update item (stock, price, status) |
| POST | /orders | Place an order (validates & deducts stock) |
| GET | /orders/{orderId} | Get order details |

## CI/CD Pipeline

Every push to `main`:
1. Runs pytest unit tests (80% coverage gate)
2. Terraform provisions AWS infrastructure as code
3. Packages and deploys Lambda functions
4. Smoke tests the live API endpoint

Pull requests run tests only — no deployment.

## Quick Start

### 1. Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform installed
- Python 3.11+

### 2. Bootstrap (run once)
```bash
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

### 3. Deploy locally
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. Run tests
```bash
pip install -r requirements.txt
pytest tests/ -v --cov=src
```

## GitHub Actions Setup

Add these secrets to your GitHub repo (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key |

Push to `main` — the pipeline runs automatically.

## Sample Requests

### Create an inventory item
```bash
curl -X POST $API_ENDPOINT/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "sku": "LAP-001", "price": 999.99, "quantity": 50, "category": "electronics"}'
```

### Place an order
```bash
curl -X POST $API_ENDPOINT/orders \
  -H "Content-Type: application/json" \
  -d '{"customerId": "cust-123", "lineItems": [{"itemId": "<item-id>", "quantity": 2}]}'
```

### Get order status
```bash
curl $API_ENDPOINT/orders/<order-id>
```

## Project Structure

```
erp-inventory-api/
├── .github/workflows/
│   └── deploy.yml          # CI/CD pipeline
├── src/
│   ├── items/handler.py    # Inventory Lambda
│   ├── orders/handler.py   # Orders Lambda
│   └── common/             # Shared utilities
├── terraform/
│   ├── main.tf             # Infrastructure as code
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/api_method/ # Reusable API module
├── tests/                  # Unit tests (pytest)
├── scripts/bootstrap.sh    # One-time AWS setup
└── requirements.txt
```

## Key Design Decisions

- **Serverless** — Lambda + API Gateway scales to zero, no server management
- **IaC** — All infrastructure defined in Terraform, no manual AWS console clicks
- **Least privilege IAM** — Lambda role has only the DynamoDB permissions it needs
- **Stock validation** — Orders check inventory levels before confirming, deduct atomically
- **Test gates** — Pipeline blocks deployment if tests fail or coverage drops below 80%
