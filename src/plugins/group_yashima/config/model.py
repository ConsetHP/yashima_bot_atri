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
    report_title: str
    big_banner: bool
    week_bar_plot: bool
    day_bar_plot: bool


class Sender(BaseModel):
    message_send_interval: float
    message_send_retry: int
    target_guild: str
    target_group: int
