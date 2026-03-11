from enum import Enum


class ChannelType(str, Enum):
    DINGTALK = "dingtalk"
    WECHAT = "wechat"
    FEISHU = "feishu"


class NotificationScene(str, Enum):
    SIGNAL = "signal"
    ALERT = "alert"
    REPORT = "report"