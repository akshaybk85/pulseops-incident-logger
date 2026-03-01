data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  

  filter {
    name   = "name"
    values = ["ubuntu*24.04*amd64*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
    filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}
