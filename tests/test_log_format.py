"""日志格式测试：ISO 8601 本地时区时间戳（脚手架地基能力，见 BOOTSTRAP_CONTRACT.md）。

覆盖:
- 访问日志时间戳 → test_access_log_has_iso_timestamp
- 启动日志时间戳 → test_startup_log_has_iso_timestamp
- setup_logging 幂等性   → test_setup_logging_applies_local_formatters_and_is_idempotent
- local_iso 输出格式     → test_local_iso_format

依赖: httpx2（dev 组，starlette TestClient 使用）
"""

import logging
import re
from datetime import datetime

from fastapi.testclient import TestClient

from src.logging_config import (
    ACCESS_FMT,
    DEFAULT_FMT,
    LocalAccessFormatter,
    LocalDefaultFormatter,
    local_iso,
    setup_logging,
)
from src.main import APP_NAME, APP_VERSION, app

# 契约: 本地时区 + 毫秒定长 + 数字偏移（如 +08:00；UTC 主机为 +00:00）
ISO_LOCAL = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}"

# uvicorn access logger 的原始 msg 与 args 结构，AccessFormatter.formatMessage 依赖它解包
ACCESS_MSG = '%s - "%s %s HTTP/%s" %d'
ACCESS_ARGS = ("10.10.4.11:61035", "GET", "/api/example", "1.1", 200)


class _CaptureHandler(logging.Handler):
    def __init__(self, level: int = logging.INFO) -> None:
        super().__init__(level)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _access_record() -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=ACCESS_MSG,
        args=ACCESS_ARGS,
        exc_info=None,
    )


def test_access_log_has_iso_timestamp():
    line = LocalAccessFormatter(fmt=ACCESS_FMT, use_colors=False).format(_access_record())

    assert re.fullmatch(
        rf'INFO: \[{ISO_LOCAL}\] 10\.10\.4\.11:61035 - "GET /api/example HTTP/1\.1" 200 OK',
        line,
    ), line


def test_startup_log_has_iso_timestamp():
    handler = _CaptureHandler()
    logger = logging.getLogger("uvicorn.error")
    logger.addHandler(handler)
    try:
        # TestClient 作为上下文管理器才会触发 lifespan 启动事件，无需业务路由
        with TestClient(app):
            pass
    finally:
        logger.removeHandler(handler)

    messages = [record for record in handler.records if "启动完成" in record.getMessage()]
    assert messages, "未捕获到服务启动日志"

    # 时间戳来自格式串而非消息体，因此用同一 formatter 渲染整行再校验
    line = LocalDefaultFormatter(fmt=DEFAULT_FMT, use_colors=False).format(messages[0])
    expected = rf"INFO: \[{ISO_LOCAL}\] {re.escape(APP_NAME)} v{re.escape(APP_VERSION)} 启动完成"
    assert re.fullmatch(expected, line), line


def test_setup_logging_applies_local_formatters_and_is_idempotent():
    setup_logging()
    setup_logging()

    uvicorn_logger = logging.getLogger("uvicorn")
    access_logger = logging.getLogger("uvicorn.access")

    assert len(uvicorn_logger.handlers) == 1, "重复 setup_logging 不应叠加 handler"
    assert len(access_logger.handlers) == 1, "重复 setup_logging 不应叠加 handler"
    assert isinstance(uvicorn_logger.handlers[0].formatter, LocalDefaultFormatter)
    assert isinstance(access_logger.handlers[0].formatter, LocalAccessFormatter)


def test_local_iso_format():
    assert re.fullmatch(ISO_LOCAL, local_iso())

    # 固定 epoch 校验：输出必须等于“系统本地时区”下的 ISO 8601，且偏移与宿主机一致
    epoch = 0.0
    expected = datetime.fromtimestamp(epoch).astimezone().isoformat(timespec="milliseconds")
    assert local_iso(epoch) == expected
    assert datetime.fromisoformat(local_iso()).utcoffset() == datetime.now().astimezone().utcoffset()
