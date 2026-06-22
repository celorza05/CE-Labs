"""Post messages to Slack via Incoming Webhook or bot token.

Degrades gracefully: if neither a webhook URL nor a bot token is configured,
the message is logged locally and ``notify`` returns False (the pipeline still
runs — you just don't get Slack notifications).
"""

from __future__ import annotations

import logging

from . import config

log = logging.getLogger("orchestrator.slack")


def notify(text: str) -> bool:
    """Send ``text`` to Slack. Returns True if it was delivered."""
    if config.SLACK_WEBHOOK_URL:
        return _post_webhook(text)
    if config.SLACK_BOT_TOKEN:
        return _post_bot(text)
    log.info("Slack not configured — message follows:\n%s", text)
    return False


def _post_webhook(text: str) -> bool:
    import requests

    try:
        resp = requests.post(config.SLACK_WEBHOOK_URL, json={"text": text}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as exc:  # never let a Slack hiccup break the pipeline
        log.warning("Slack webhook failed: %s", exc)
        return False


def _post_bot(text: str) -> bool:
    import requests

    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {config.SLACK_BOT_TOKEN}"},
            json={"channel": config.SLACK_CHANNEL, "text": text},
            timeout=15,
        )
        data = resp.json()
        if not data.get("ok"):
            log.warning("Slack API error: %s", data.get("error"))
            return False
        return True
    except Exception as exc:
        log.warning("Slack post failed: %s", exc)
        return False
