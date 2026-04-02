#!/bin/bash
# Run this ONCE before anything else to create the S3 bucket
# that stores your Terraform state remotely.
# Usage: chmod +x scripts/bootstrap.sh && ./scripts/bootstrap.sh

set -e

BUCKET_NAME="erp-inventory-tfstate"
REGION="us-east-1"

echo "Creating S3 bucket for Terraform state: $BUCKET_NAME"

aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION"

aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo ""
echo "Bootstrap complete. S3 bucket '$BUCKET_NAME' is ready."
echo "Now run: cd terraform && terraform init"
