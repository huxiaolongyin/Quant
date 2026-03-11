from backend.notifiers.base import BaseNotifier
from backend.notifiers.dingtalk import DingTalkNotifier
from backend.notifiers.feishu import FeishuNotifier
from backend.notifiers.wechat import WeChatNotifier

__all__ = ["BaseNotifier", "DingTalkNotifier", "WeChatNotifier", "FeishuNotifier"]


def get_notifier(channel_type: str, webhook_url: str, secret: str = None) -> BaseNotifier:
    notifiers = {
        "dingtalk": DingTalkNotifier,
        "wechat": WeChatNotifier,
        "feishu": FeishuNotifier,
    }
    notifier_class = notifiers.get(channel_type)
    if not notifier_class:
        raise ValueError(f"Unsupported channel type: {channel_type}")
    return notifier_class(webhook_url=webhook_url, secret=secret)