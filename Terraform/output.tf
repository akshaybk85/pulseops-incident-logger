output "server_public_ip" {
  description = "Public ip of Pulseops server"
  value       = aws_instance.pulseops_server.public_ip
}

output "server_public_dns" {
  description = "Public DNS of Pulseops server"
  value       = aws_instance.pulseops_server.public_dns

}

output "grafana_url" {
  description = "URL to access Grafana"
  value       = "http://${aws_instance.pulseops_server.public_ip}:3000"

}

output "prometheus_url" {

  description = "URL to access Prometheus"
  value       = "http://${aws_instance.pulseops_server.public_ip}:9090"
}