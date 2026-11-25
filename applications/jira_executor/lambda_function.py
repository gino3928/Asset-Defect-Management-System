"""Apply an exact, authorized proposal to Jira without involving a language model."""

import json
import os
import time
import urllib.request

import boto3
from boto3.dynamodb.conditions import Attr


secrets = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")


def _post_to_slack(response_url, text):
    if not response_url:
        return
    request = urllib.request.Request(
        response_url,
        data=json.dumps({"response_type": "ephemeral", "replace_original": True, "text": text}).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5):
        pass


def _authorized(user_id):
    item = dynamodb.Table(os.environ["AUTHORIZATION_TABLE_NAME"]).get_item(
        Key={"SlackUserId": user_id}, ConsistentRead=True
    ).get("Item", {})
    return item.get("Enabled") is True and item.get("Role") in {"defect_operator", "defect_admin"}


def _jira_update(issue_key, fields):
    credential = json.loads(secrets.get_secret_value(SecretId=os.environ["JIRA_SECRET_ARN"])["SecretString"])
    url = f"https://api.atlassian.com/ex/jira/{credential['cloud_id']}/rest/api/3/issue/{issue_key}"
    request = urllib.request.Request(
        url,
        data=json.dumps({"fields": fields}).encode("utf-8"),
        headers={
            "authorization": f"Bearer {credential['api_token']}",
            "accept": "application/json",
            "content-type": "application/json",
        },
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status not in {200, 204}:
            raise RuntimeError(f"Jira returned HTTP {response.status}")


def lambda_handler(event, _context):
    user_id = event.get("user_id", "")
    response_url = event.get("response_url", "")
    if not _authorized(user_id):
        _post_to_slack(response_url, "Authorization failed; Jira was not changed.")
        return {"status": "DENIED"}

    action = event.get("action")
    if action not in {"defect_confirm", "defect_cancel"}:
        _post_to_slack(response_url, "Unsupported action; Jira was not changed.")
        return {"status": "DENIED"}

    table = dynamodb.Table(os.environ["PROPOSAL_TABLE_NAME"])
    proposal_id = event["proposal_id"]
    proposal = table.get_item(Key={"ProposalId": proposal_id}, ConsistentRead=True).get("Item")
    if not proposal or proposal.get("Status") != "PENDING":
        _post_to_slack(response_url, "This proposal is missing or has already been handled.")
        return {"status": "IGNORED"}

    if action == "defect_cancel":
        table.update_item(
            Key={"ProposalId": proposal_id},
            UpdateExpression="SET #status = :cancelled, DecidedBy = :user, DecidedAt = :now",
            ConditionExpression=Attr("Status").eq("PENDING"),
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={":cancelled": "CANCELLED", ":user": user_id, ":now": int(time.time())},
        )
        _post_to_slack(response_url, f"Proposal for {proposal['IssueKey']} was cancelled. Jira was not changed.")
        return {"status": "CANCELLED"}

    # Only the validated Confirm action reaches this Jira write path.
    table.update_item(
        Key={"ProposalId": proposal_id},
        UpdateExpression="SET #status = :applying, DecidedBy = :user, DecidedAt = :now",
        ConditionExpression=Attr("Status").eq("PENDING"),
        ExpressionAttributeNames={"#status": "Status"},
        ExpressionAttributeValues={":applying": "APPLYING", ":user": user_id, ":now": int(time.time())},
    )
    fields = {"priority": {"name": proposal["PriorityName"]}}
    if proposal.get("AssigneeAccountId"):
        fields["assignee"] = {"accountId": proposal["AssigneeAccountId"]}

    try:
        _jira_update(proposal["IssueKey"], fields)
        table.update_item(
            Key={"ProposalId": proposal_id},
            UpdateExpression="SET #status = :applied, AppliedAt = :now",
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={":applied": "APPLIED", ":now": int(time.time())},
        )
        _post_to_slack(response_url, f"Applied the approved proposal to {proposal['IssueKey']}.")
        return {"status": "APPLIED"}
    except Exception as exc:
        table.update_item(
            Key={"ProposalId": proposal_id},
            UpdateExpression="SET #status = :failed, FailureReason = :reason",
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={":failed": "FAILED", ":reason": str(exc)[:500]},
        )
        _post_to_slack(response_url, f"Jira update failed for {proposal['IssueKey']}; the proposal is marked FAILED.")
        raise
