"""Verify Slack requests and route them to isolated workflow boundaries."""

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse

import boto3


secrets = boto3.client("secretsmanager")
sqs = boto3.client("sqs")
lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")
_signing_secret = None


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def _raw_body(event):
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        return base64.b64decode(body).decode("utf-8")
    return body


def _secret():
    global _signing_secret
    if _signing_secret is None:
        value = secrets.get_secret_value(SecretId=os.environ["SLACK_SECRET_ARN"])
        _signing_secret = json.loads(value["SecretString"])["signing_secret"]
    return _signing_secret


def _verified(event, raw_body):
    headers = {key.lower(): value for key, value in (event.get("headers") or {}).items()}
    timestamp = headers.get("x-slack-request-timestamp", "")
    signature = headers.get("x-slack-signature", "")
    try:
        if abs(time.time() - int(timestamp)) > 300:
            return False
    except ValueError:
        return False
    message = f"v0:{timestamp}:{raw_body}".encode("utf-8")
    expected = "v0=" + hmac.new(_secret().encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _authorized(slack_user_id):
    table = dynamodb.Table(os.environ["DEFECT_AUTHORIZATION_TABLE"])
    item = table.get_item(Key={"SlackUserId": slack_user_id}, ConsistentRead=True).get("Item", {})
    return item.get("Enabled") is True and item.get("Role") in {"defect_operator", "defect_admin"}


def _handle_command(form):
    if form.get("team_id") != os.environ["SLACK_WORKSPACE_ID"]:
        return _response(403, {"response_type": "ephemeral", "text": "Workspace is not authorized."})

    command = form.get("command")
    user_id = form.get("user_id", "")
    if command == "/defect-agent" and not _authorized(user_id):
        return _response(200, {"response_type": "ephemeral", "text": "You are not authorized to use /defect-agent."})
    if command not in {"/asset-agent", "/defect-agent"}:
        return _response(400, {"response_type": "ephemeral", "text": "Unsupported command."})

    queue_url = os.environ["ASSET_QUEUE_URL"] if command == "/asset-agent" else os.environ["DEFECT_QUEUE_URL"]
    message = {
        "kind": "command",
        "command": command,
        "text": form.get("text", "").strip(),
        "user_id": user_id,
        "channel_id": form.get("channel_id", ""),
        "team_id": form.get("team_id", ""),
        "response_url": form.get("response_url", ""),
        "trigger_id": form.get("trigger_id", ""),
    }
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
    return _response(200, {"response_type": "ephemeral", "text": f"{command} request accepted for processing."})


def _handle_interaction(payload):
    if payload.get("team", {}).get("id") != os.environ["SLACK_WORKSPACE_ID"]:
        return _response(403, {"text": "Workspace is not authorized."})
    action = (payload.get("actions") or [{}])[0]
    if action.get("action_id") not in {"defect_confirm", "defect_cancel"}:
        return _response(400, {"text": "Unsupported action."})

    # The executor rechecks authorization and proposal state before any Jira write.
    event = {
        "action": action["action_id"],
        "proposal_id": action.get("value", ""),
        "user_id": payload.get("user", {}).get("id", ""),
        "response_url": payload.get("response_url", ""),
    }
    lambda_client.invoke(
        FunctionName=os.environ["JIRA_EXECUTOR_FUNCTION_NAME"],
        InvocationType="Event",
        Payload=json.dumps(event).encode("utf-8"),
    )
    return _response(200, {"response_type": "ephemeral", "replace_original": False, "text": "Action received."})


def lambda_handler(event, _context):
    raw_body = _raw_body(event)
    if not _verified(event, raw_body):
        return _response(401, {"text": "Invalid Slack signature."})

    form = urllib.parse.parse_qs(raw_body, keep_blank_values=True)
    flat = {key: values[0] for key, values in form.items()}
    if "payload" in flat:
        return _handle_interaction(json.loads(flat["payload"]))
    return _handle_command(flat)

