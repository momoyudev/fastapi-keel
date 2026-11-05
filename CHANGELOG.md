# CHANGELOG — 脚手架底座变更

> 本文件记录 `fastapi-keel` 脚手架仓库自身的底座演进（环境、工具链、骨架目录、基础命令）。
> 当前有效基线见 `BOOTSTRAP_CONTRACT.md`；git 历史已按模板基线重置，历史明细见本文件。
> 用本仓库初始化新项目后，可按需清空本文件；本文件不跟踪业务 Feature 进度。

| 日期 | 触发 | 变更 | 冒烟重校验 | 人工复核 |
|---|---|---|---|---|
| 2026-11-05 | 人工要求 Docker 日志时间格式与宿主机一致 | `Dockerfile` 最终镜像新增 `ARG TZ=Asia/Shanghai` + `ENV TZ=${TZ}`，并加构建期检查 `test -f /usr/share/zoneinfo/${TZ}` 防止时区数据缺失时静默回退 UTC；默认日志带 `+08:00`，可用 `--build-arg TZ=...` 或运行时 `-e TZ=...` 覆盖；README 时区 FAQ 同步更新。`python:3.12-slim` 自带 tzdata，无需 apt 安装 | ✅ 实测 `docker build` 成功、容器 `/openapi.json → 200`，日志为 `2026-11-05T11:08:11.456+08:00`；另以 `--build-arg TZ=UTC` 构建验证输出为 `+00:00` | [x] |
| 2026-11-05 | 人工要求日志时间与系统本地时间一致（原 UTC 输出与系统相差 8 小时） | `src/logging_config.py` 时间戳由 UTC（`...Z`）改为系统本地时区 ISO 8601（毫秒定长 + 数字偏移，如 `2026-11-05T10:59:19.337+08:00`）；类/函数更名为 `LocalAccessFormatter` / `LocalDefaultFormatter` / `local_iso`；同步更新 `tests/test_log_format.py`、`src/main.py` 注释、README 目录说明与时区 FAQ。注：Docker 容器默认 `TZ=UTC`，容器日志需与宿主机一致时运行时传 `-e TZ=Asia/Shanghai`（基础镜像需含 tzdata） | ✅ pytest 6 passed、ruff check . All checks passed、pyright 0 errors；实测 uvicorn 启动/访问日志均为 `+08:00` | [x] |
| 2026-11-04 | 人工要求将项目重置为脚手架模板 | 移除业务实现（/api/auth/token、/api/auth/refresh、/api/now-time、/api/getos 及其 config、auth、system_info 模块与对应测试）；proposal.json 重置为空白提案模板（status=discussing）；feature_list.json 清空为空数组；proposal_archive/ 清空；验收历史一并清除；UTC 日志能力保留为地基并纳入骨架清单；新增 README 脚手架使用说明 | ✅ pytest 6 passed（2 冒烟 + 4 日志）、ruff check . All checks passed、pyright 0 errors、uvicorn OK | [x] |
| 2026-11-04 | 人工确认改造为 uv 虚拟项目 | `pyproject.toml` 移除 `[build-system]` 与 `[project.scripts]`，删除 `src/harness/` 占位包：项目不打包、不安装自身，`name` 解耦为纯标识（脚手架改名只需改 name + `uv lock`）；`.dockerignore` 同步移除 `src/harness/`；uv.lock 重新生成 | ✅ `uv lock` Resolved 28 packages、pytest 6 passed、ruff All checks passed、pyright 0 errors、uvicorn OK；另以临时副本实测改名 `my-order-service` 后 lock/sync/pytest 全通过 | [x] |
| 2026-11-04 | Dockerfile 随虚拟项目精简 | COPY 清单移除 README.md（虚拟项目不构建自身，不再读取 readme 字段）；移除 `COPY src` 后的第二次 `uv sync`（无项目可安装，属空操作）；注释补充「补回 build-system 时需恢复 README.md 与二次 sync」的提示 | ✅ 真实 `docker build` 成功 + 容器启动 `/docs → 200`，启动日志带 UTC 时间戳；本地另验证无 README.md 时 `uv sync --frozen` 正常、deps-only venv 可启动服务 | [x] |
| 2026-11-04 | 人工选定脚手架名称 | 定名 `fastapi-keel`（规避与 Harness.io DevOps 平台的搜索撞名）；`pyproject.toml` name、`src/main.py` APP_NAME、README 标题与 Docker 镜像 tag 同步更新；uv.lock 重新生成。`harness/` 目录与"Harness 流程"名称不变（指流程体系，非产品名） | ✅ pytest 6 passed、ruff check . All checks passed、pyright 0 errors | [x] |
