"""飞书 Webhook 机器人通知"""

import json
import urllib.error
import urllib.request
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_TIMEOUT = 5  # 秒


def send_feishu_card(webhook_url: str, title: str, content: str, color: str = "red") -> bool:
    """发送富文本卡片消息到飞书群机器人

    Args:
        webhook_url: 飞书自定义机器人 Webhook 地址
        title: 卡片标题
        content: Markdown 正文
        color: 卡片颜色 (red/orange/blue/green/grey)

    Returns:
        是否发送成功
    """
    payload: dict[str, Any] = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "elements": [
                {"tag": "markdown", "content": content},
            ],
        },
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("code") != 0:
                logger.warning("Feishu webhook responded with error: %s", body)
                return False
            return True
    except urllib.error.URLError as e:
        logger.warning("Failed to send Feishu notification: %s", e)
        return False


def format_sentry_issue_alert(payload: dict[str, Any]) -> tuple[str, str, str]:
    """将 Sentry Issue Alert webhook payload 格式化为飞书卡片

    Returns:
        (title, content, color)
    """
    # Sentry issue alert 字段
    project = payload.get("project", {})
    project_name = project.get("slug", "unknown") if isinstance(project, dict) else str(project)

    title = payload.get("title") or payload.get("message") or "Unknown Error"
    culprit = payload.get("culprit", "")
    level = (payload.get("level") or "error").upper()
    issue_url = payload.get("url", "")
    count = payload.get("count", "?")
    first_seen = payload.get("first_seen", "")
    last_seen = payload.get("last_seen", "")
    users_count = payload.get("users", {}).get("count", "?") if isinstance(payload.get("users"), dict) else "?"

    # event 子对象（可能存在）
    event = payload.get("event") or {}
    environment = ""
    tags: list[tuple[str, str]] = []

    if isinstance(event, dict):
        environment = event.get("environment", "")
        event_url = event.get("url", "")
        if event_url and not issue_url:
            issue_url = event_url
        for tag in event.get("tags", []):
            if isinstance(tag, (list, tuple)) and len(tag) >= 2:
                tags.append((tag[0], tag[1]))

    tags_str = ", ".join(f"{k}={v}" for k, v in tags) if tags else "-"
    env_display = environment or "-"

    # 飞书卡片标题
    card_title = f"[Sentry {level}] {project_name}"

    # 飞书卡片正文 (飞书 markdown)
    lines = [
        f"**{title}**",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| Project | {project_name} |",
        f"| Environment | {env_display} |",
        f"| Level | {level} |",
        f"| 发生次数 | {count} |",
        f"| 影响用户 | {users_count} |",
    ]
    if culprit:
        lines.append(f"| 位置 | `{culprit}` |")
    if first_seen:
        lines.append(f"| 首次出现 | {first_seen} |")
    if last_seen:
        lines.append(f"| 最近出现 | {last_seen} |")
    if tags_str != "-":
        lines.append(f"| Tags | {tags_str} |")
    if issue_url:
        lines.extend(["", f"[查看详情]({issue_url})"])

    content = "\n".join(lines)

    color_map = {"FATAL": "red", "ERROR": "red", "WARNING": "orange"}
    color = color_map.get(level, "blue")

    return card_title, content, color
