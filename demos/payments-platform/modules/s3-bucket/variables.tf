variable "name" {
  type        = string
  description = "Bucket name prefix; env is appended."
}

variable "env" {
  type        = string
  description = "Environment (dev|prod)."
  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "env must be dev or prod."
  }
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Extra tags."
}
