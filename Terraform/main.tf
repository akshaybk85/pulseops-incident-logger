resource "aws_security_group" "pulseops_sg" {
  name        = "pulseops-sg"
  description = "Security group for PulseOps server"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow SSH from anywhere (not recommended for production)

  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow HTTP from anywhere

  }

  # Grafana

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow access to port 3000 from anywhere
  }

  # Alertmanager

  ingress {
    from_port   = 9093
    to_port     = 9093
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow access to port 9093 from anywhere
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow access to port 9090 from anywhere

  }
  #Loki

  ingress {
    from_port   = 3100
    to_port     = 3100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow access to port 3100 from anywhere

  }
  #AI Responder

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow access to port 5000 from anywhere
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # Allow all outbound traffic
  }

}

resource "aws_key_pair" "pulseops-key" {
  key_name   = "pulseops-key"
  public_key = file(var.public_key_path)
}





resource "aws_instance" "pulseops_server" {
  ami             = data.aws_ami.ubuntu.id
  instance_type   = var.instance_type
  key_name = aws_key_pair.pulseops-key.key_name
  vpc_security_group_ids = [aws_security_group.pulseops_sg.id]

  root_block_device {

    volume_size = 20
    volume_type = "gp2"
  }


  user_data = <<-EOF
                #!/bin/bash
                sudo apt update -y
                sudo apt install -y docker.io docker-compose git
                usermod -aG docker $user
                sudo systemctl start docker
                sudo systemctl enable docker
                EOF
  tags = {
    Name    = "pulseops-server"
    Project = "Pulseops"
  }

}

