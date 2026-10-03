variable "aws_region" {
  description = "AWS Region (default is ap-southeast-2 to comply with lab IAM/SCP restrictions)"
  type        = string
  default     = "ap-southeast-2"
}

variable "hf_token" {
  description = "Hugging Face Token for gated models (like Gemma)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "model_id" {
  description = "Hugging Face Model ID to serve"
  type        = string
  default     = "google/gemma-4-E2B-it"
}

variable "enable_gpu" {
  description = "Set to true to deploy the optional GPU + vLLM LLM inference node instead of the default CPU + LightGBM node"
  type        = bool
  default     = false
}

variable "cpu_instance_type" {
  description = "Instance type for CPU compute node (t3.micro for Free-Tier policy compliance, or t3.medium if quota permits)"
  type        = string
  default     = "t3.micro"
}

variable "gpu_instance_type" {
  description = "Instance type for the optional GPU (vLLM) compute node"
  type        = string
  default     = "g4dn.xlarge"
}