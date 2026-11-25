output "slack_commands_url" {
  description = "Slack slash-command request URL."
  value       = "${aws_apigatewayv2_api.slack.api_endpoint}/slack/commands"
}

output "slack_interactions_url" {
  description = "Slack interactive-component request URL."
  value       = "${aws_apigatewayv2_api.slack.api_endpoint}/slack/interactions"
}

output "slack_secret_arn" { value = aws_secretsmanager_secret.slack.arn }
output "jira_read_secret_arn" { value = aws_secretsmanager_secret.jira_read.arn }
output "jira_secret_arn" { value = aws_secretsmanager_secret.jira.arn }
output "defect_agentcore_harness_arn" { value = aws_bedrockagentcore_harness.defect_review.arn }
output "asset_integrations_secret_arn" { value = aws_secretsmanager_secret.asset_integrations.arn }
output "defect_authorization_table" { value = module.defect_authorization.name }
output "defect_proposals_table" { value = module.defect_proposals.name }
output "asset_dlq_arn" { value = module.asset_queue.dlq_arn }
output "defect_dlq_arn" { value = module.defect_queue.dlq_arn }
