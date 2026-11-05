# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
# uv 版本与本地开发环境对齐（.venv/pyvenv.cfg: uv = 0.13.6）
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
# 不装开发依赖
ENV UV_NO_DEV=1
# 不要uv自动下载python，使用基础镜像自带python
ENV UV_PYTHON_DOWNLOADS=0

# 本项目为 uv 虚拟项目（pyproject 无 [build-system]）：uv 不构建/安装项目自身，只装运行时依赖；
# 依赖清单单独成层以利用构建缓存。若将来补回 [build-system] 打包，
# 需把 README.md（pyproject 的 readme 字段）加回 COPY，并在 COPY src 后重新 sync 安装项目。
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-cache

# 保留 src 布局，镜像内启动方式与项目契约一致：uvicorn src.main:app
COPY src ./src

# 最终镜像
FROM python:3.12-slim
# 日志时区与宿主机保持一致：容器默认 TZ=UTC，会让日志时间少 8 小时。
# 默认 Asia/Shanghai；其他时区可用 docker build --build-arg TZ=Europe/London 覆盖。
# python:3.12-slim 自带 tzdata（/usr/share/zoneinfo），无需额外 apt 安装。
ARG TZ=Asia/Shanghai
ENV TZ=${TZ}
# 时区数据缺失时 TZ 会静默回退为 UTC，构建期直接失败更易发现。
RUN test -f "/usr/share/zoneinfo/${TZ}"

ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
# 把venv加到PATH，直接python调用
ENV PATH="/app/.venv/bin:$PATH"

# 非 root 运行
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --create-home appuser
USER appuser

EXPOSE 8000
# 必须绑 0.0.0.0，否则容器外访问不到
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
