from pydantic import BaseModel


class Config(BaseModel):
    general: "General"
    notice: "Notice"
    db: "DataBase"
    analyzer: "Analyzer"
    sender: "Sender"


class General(BaseModel):
    bot_qq_id: str
    """机器人 QQ 号"""
    bot_admin_tiny_id: int
    """机器人管理员 tiny id，与QQ号不通用"""


class Notice(BaseModel):
    user: str
    """通知邮箱"""
    host: str
    """通知邮箱对应的SMTP服务器域名"""
    port: int
    """SMTP服务器端口"""
    key: str
    """SMTP服务器授权码"""


class DataBase(BaseModel):
    file_name: str
    """数据库文件名"""


class Analyzer(BaseModel):
    target_group: int
    """要分析的QQ群的群id"""
    report_title: str
    """报告的标题"""
    big_banner: bool
    """报告是否包含大banner"""
    week_bar_plot: bool
    """报告是否包含周消息柱状图"""
    day_bar_plot: bool
    """报告是否包含日消息柱状图"""


class Sender(BaseModel):
    message_send_interval: float
    """消息发送间隔，单位：秒"""
    message_send_retry: int
    """消息重试次数"""
    target_guild: str
    """发送消息的频道id"""
    target_group: int
    """发送消息的群id"""
