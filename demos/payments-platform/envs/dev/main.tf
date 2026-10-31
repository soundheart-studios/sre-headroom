terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  backend "s3" {
    bucket       = "acme-tfstate-dev"
    key          = "payments/dev.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
  }
}

provider "aws" {
  region = "eu-west-1"
  default_tags { tags = { system = "payments", env = "dev" } }
}

module "ledger_exports" {
  source = "../../modules/s3-bucket"
  name   = "acme-ledger-exports"
  env    = "dev"
}

# Legacy bucket created before G-0001; not yet migrated to the module.
resource "aws_s3_bucket" "receipts" {
  bucket = "acme-payment-receipts-dev"
}

data "aws_iam_policy_document" "worker" {
  statement {
    actions   = ["s3:*"]
    resources = ["${module.ledger_exports.bucket_arn}/*"]
  }
}

resource "aws_iam_policy" "worker" {
  name   = "payments-worker-dev"
  policy = data.aws_iam_policy_document.worker.json
}
