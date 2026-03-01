variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "ap-south-1" # You can change this to your preferred region

}
variable "instance_type" {
  description = "The type of AWS instance to deploy"
  type        = string
  default     = "t3.medium" # You can change this to your preferred instance type

}

variable "public_key_path" {
  description = "The file path to the public key for SSH access"
  type        = string
  default     = "~/.ssh/pulseops.pub" # You can change this to the path of your public key

}