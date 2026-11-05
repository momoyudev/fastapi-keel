# src/main.py
"""服务入口骨架：仅实例化 FastAPI app，不含任何业务路由。

业务路由在实现编码阶段添加：proposal.json.status=accepted 后，
按 feature_list.json 的验收标准在 create_app() 内注册路由，
并编写对应业务单元测试，由 scripts/verifier.py 逐条验收。
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.logging_config import setup_logging

# 导入期配置日志：uvicorn 先 configure_logging() 再导入 app，此处覆盖 formatter。
# 详见 src/logging_config.py 模块注释。
setup_logging()

# TODO: 开始新项目时改成你的服务名与版本（建议同步修改 pyproject.toml 的 name/version）
APP_NAME = "fastapi-keel"
APP_VERSION = "0.1.0"

logger = logging.getLogger("uvicorn.error")  # 复用 uvicorn 已配置好 handler 的日志器，避免另建一套


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """启动时打印服务名与版本；启动时刻由日志格式串统一添加的本地时区时间戳体现。"""
    logger.info("%s v%s 启动完成", APP_NAME, APP_VERSION)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

    # TODO: 实现编码阶段在此注册业务路由（提案接受后，按 feature_list 逐条实现）
    # 示例：
    # @app.get("/api/example")
    # def example() -> dict[str, str]:
    #     return {"hello": "world"}

    return app


app = create_app()
