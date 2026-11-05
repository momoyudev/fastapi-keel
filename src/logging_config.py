"""uvicorn 日志格式配置：统一输出本地时区 ISO 8601 时间戳。

为什么在 app 导入期配置，而不是用 `--log-config` 文件：
- 保持启动命令 `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload` 不变；
- uvicorn 0.54.0 的 `Config.__init__` 会先调用 `configure_logging()`，随后 `load()`
  才导入 app（见 uvicorn/config.py），因此 app 导入期的 dictConfig 必然后执行并生效；
- `--reload` 下 app 在 worker 进程导入，配置只作用于真正处理请求的进程。

时间戳为什么不用 `%(asctime)s` 的默认渲染：
- 默认毫秒分隔符是逗号，且没有时区后缀，不满足 ISO 8601 契约；
- 这里改用系统本地时区，并在末尾保留数字偏移（如 `+08:00`），
  既能与宿主机 `date` 输出一致，也不会因省略时区而产生歧义。
"""

from __future__ import annotations

import copy
import logging
import logging.config
from datetime import datetime
from typing import Any

from uvicorn.config import LOGGING_CONFIG
from uvicorn.logging import AccessFormatter, DefaultFormatter

# 访问日志：保留 client_addr / request_line / status_code，前面加本地时间戳
# 用 %(levelname)s 而非 uvicorn 的 %(levelprefix)s：后者会把级别名补齐到 8 字符
# （INFO: + 4 空格），与时间戳连排时空隙过大；代价是 TTY 下不再有级别颜色。
ACCESS_FMT = '%(levelname)s: [%(asctime)s] %(client_addr)s - "%(request_line)s" %(status_code)s'
# 服务日志（启动、异常）：消息前统一加本地时间戳
DEFAULT_FMT = "%(levelname)s: [%(asctime)s] %(message)s"


def local_iso(timestamp: float | None = None) -> str:
    """返回系统本地时区 ISO 8601 时间戳（毫秒定长 + 数字偏移）。

    例：2026-11-05T10:56:06.601+08:00
    """
    moment = datetime.now().astimezone() if timestamp is None else datetime.fromtimestamp(timestamp).astimezone()
    return moment.isoformat(timespec="milliseconds")


class _LocalTimestampMixin:
    """把 logging 默认的本地时间 asctime 换成带时区偏移的 ISO 8601。"""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        # 用 record.created（事件发生时刻）而非格式化时刻，避免延迟影响时间精度
        return local_iso(record.created)


class LocalAccessFormatter(_LocalTimestampMixin, AccessFormatter):
    """访问日志 formatter：本地时间戳 + uvicorn 原有的请求字段。"""


class LocalDefaultFormatter(_LocalTimestampMixin, DefaultFormatter):
    """服务日志 formatter：本地时间戳 + 级别名。"""


def build_logging_config() -> dict[str, Any]:
    """基于 uvicorn 默认配置派生，只替换 formatter，handler/logger 结构保持不变。"""
    config: dict[str, Any] = copy.deepcopy(LOGGING_CONFIG)
    config["formatters"]["default"] = {
        "()": LocalDefaultFormatter,
        "fmt": DEFAULT_FMT,
        "use_colors": None,
    }
    config["formatters"]["access"] = {
        "()": LocalAccessFormatter,
        "fmt": ACCESS_FMT,
    }
    return config


def setup_logging() -> None:
    """应用日志配置。幂等：重复调用只是整体替换 handler，不会叠加出重复日志行。"""
    logging.config.dictConfig(build_logging_config())
