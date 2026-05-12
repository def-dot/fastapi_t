"""Webhook 路由 — 接收 Sentry Alert 回调并转发飞书"""

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Header, Request

from app.core.config import settings
from app.core.feishu import format_sentry_issue_alert, send_feishu_card
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_sentry_signature(body: bytes, signature: str | None) -> bool:
    """验证 Sentry Webhook 签名 (HMAC-SHA256)

    如果未配置 SENTRY_WEBHOOK_SECRET 则跳过验证。
    """
    if not settings.SENTRY_WEBHOOK_SECRET:
        return True
    if not signature:
        return False
    expected = hmac.new(
        settings.SENTRY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/sentry-alert")
async def sentry_alert(
    request: Request,
    sentry_hook_signature: str | None = Header(None, alias="Sentry-Hook-Signature"),
    sentry_hook_resource: str | None = Header(None, alias="Sentry-Hook-Resource"),
) -> dict[str, Any]:
    """接收 Sentry Issue Alert webhook，转发到飞书"""
    body = await request.body()

    # 签名验证
    if not _verify_sentry_signature(body, sentry_hook_signature):
        logger.warning("Sentry webhook signature verification failed")
        return {"status": "rejected"}

    payload = await request.json()

    resource = sentry_hook_resource or "event_alert"
    logger.info(
        "Received Sentry webhook: resource=%s, action=%s",
        resource,
        payload.get("action", {}).get("name", "-") if isinstance(payload.get("action"), dict) else "-",
    )

    if not settings.FEISHU_WEBHOOK_URL:
        logger.warning("FEISHU_WEBHOOK_URL not configured, skipping notification")
        return {"status": "skipped"}

    title, content, color = format_sentry_issue_alert(payload)
    ok = send_feishu_card(settings.FEISHU_WEBHOOK_URL, title, content, color)

    return {"status": "ok" if ok else "feishu_failed"}
