"""Initial asset workflow worker; ready to hand off to AgentCore in the next phase."""

import json
import os
import time
import urllib.request
import uuid

import boto3


dynamodb = boto3.resource("dynamodb")


def _post_to_slack(response_url, payload):
    if not response_url:
        return
    request = urllib.request.Request(
        response_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5):
        pass


def _process(message):
    now = int(time.time())
    session_id = str(uuid.uuid4())
    dynamodb.Table(os.environ["SESSION_TABLE_NAME"]).put_item(Item={
        "SessionId": session_id,
        "SlackUserId": message["user_id"],
        "RequestText": message.get("text", ""),
        "Status": "RECEIVED",
        "AgentCoreHarnessArn": os.environ.get("AGENTCORE_ARN", ""),
        "CreatedAt": now,
        "ExpiresAt": now + 86400,
    })
    dynamodb.Table(os.environ["EVENT_TABLE_NAME"]).put_item(Item={
        "EventId": str(uuid.uuid4()),
        "SessionId": session_id,
        "EventType": "ASSET_REQUEST_RECEIVED",
        "CreatedAt": now,
        "ExpiresAt": now + 604800,
    })
    text = (
        f"Asset request `{session_id}` was recorded. AgentCore execution will start when "
        "`asset_agentcore_harness_arn` is configured."
    )
    _post_to_slack(message.get("response_url"), {"response_type": "ephemeral", "text": text})


def lambda_handler(event, _context):
    failures = []
    for record in event.get("Records", []):
        try:
            _process(json.loads(record["body"]))
        except Exception:
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}

