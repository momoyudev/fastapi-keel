# fastapi-keel — Python FastAPI 后端接口脚手架

带 **Harness 流程管控**（提案 → 验收 → 归档）的 FastAPI 后端接口脚手架。
克隆本仓库作为新项目的起点：底座（工具链、目录骨架、日志、质量门禁）开箱即用，
业务代码为零，所有功能通过提案流程逐轮添加、逐条验收。

## 快速开始

前置条件：已安装 [uv](https://docs.astral.sh/uv/)（`curl -LsSf https://astral.sh/uv/install.sh | sh`）；
Python ≥ 3.12 无需单独安装（uv 按 `.python-version` 自动准备对应解释器）；
如需 Agent 协作流程，另装 OpenCode（AGENTS.md 会被自动读取生效）；Docker 仅构建镜像时需要。

```bash
# 1. 初始化环境（仅人工执行；创建 .venv 并同步依赖）
./init.sh

# 2. 地基冒烟校验
uv run pytest tests/test_bootstrap_smoke.py

# 3. 启动开发服务；浏览器打开 http://localhost:8000/docs 看到 Swagger UI 即启动成功
#    （脚手架无业务路由，docs 页仅含默认元信息属正常）
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 质量门禁
uv run pytest          # 单元测试
uv run ruff check .    # 代码检查（全仓，与实现阶段门禁一致）
uv run pyright         # 类型检查
```

Docker 构建与运行：

```bash
docker build -t fastapi-keel .
docker run -p 8000:8000 fastapi-keel
```

## 常见问题

- **端口被占用**：换端口启动（如 `--port 8001`），或先排查占用进程（`lsof -i :8000`）；
- **依赖安装慢 / 超时**：`[[tool.uv.index]]` 默认清华镜像，海外网络建议换回官方 PyPI（见"开始新项目的清单"第 3 条）；
- **Python 版本不符**：项目要求 ≥ 3.12，uv 会按 `.python-version` 自动准备，一般无需手动安装；
- **日志时间与宿主机不一致（Docker）**：镜像默认 `TZ=Asia/Shanghai`（日志带 `+08:00`）；
  其他时区可在构建时覆盖 `docker build --build-arg TZ=Europe/London -t fastapi-keel .`，
  或运行时临时覆盖 `docker run -e TZ=Europe/London -p 8000:8000 fastapi-keel`。
  基础镜像自带 tzdata，无需额外安装。

## 目录结构

```
├── AGENTS.md                  # Agent 调度入口：阶段路由逻辑与全局护栏
├── BOOTSTRAP_CONTRACT.md      # 地基契约：环境、工具链、骨架清单、冒烟校验记录
├── CHANGELOG.md               # 脚手架底座演进记录（新项目可按需清空）
├── proposal.json              # 当前轮提案（脚手架附带空白模板，status=discussing）
├── feature_list.json          # Feature 基线（顶层 features 数组，脚手架为空，条目由脚本写入）
├── proposal_archive/          # 已验收提案归档
├── harness/                   # 阶段规则（Agent 必须遵守）
│   ├── bootstrap-rules.md     #   初始化阶段
│   ├── proposal-rules.md      #   提案阶段
│   └── implementation-rules.md#   实现编码阶段
├── scripts/
│   ├── verifier.py            # Feature 验收：唯一允许写 feature 状态的工具
│   └── feature_add.py         # 从 proposal.json 草案导入 feature（--yes 才落盘）
├── src/
│   ├── main.py                # app 工厂（无业务路由，TODO 处注册路由）
│   └── logging_config.py      # 地基日志：访问/启动日志带本地时区 ISO 8601 时间戳
├── tests/
│   ├── conftest.py            # 测试隔离约定（不得依赖本地 .env / 本机密钥）
│   ├── test_bootstrap_smoke.py# 地基冒烟
│   └── test_log_format.py     # 地基日志测试
├── init.sh                    # 环境初始化（仅人工执行，Agent 禁止运行）
├── Dockerfile / .dockerignore # 生产镜像（.env 不进镜像）
├── LICENSE                    # MIT 许可证
└── .env.example               # 配置键模板（复制为 .env 使用，不提交）
```

## Harness 工作流

每轮业务迭代按阶段推进，Agent 的行为由 `AGENTS.md` 阶段路由约束：

1. **初始化（bootstrap）** —— 已完成。仅当工具链/骨架变更时重新校验，
   记录到 `BOOTSTRAP_CONTRACT.md`。
2. **提案（proposal）** —— `proposal.json.status` 为 `discussing` / `spike_required` 时生效。
   Agent 与人工讨论目标、方案对比（explorations）、风险；共同填写
   `gates.goal / constraints / exit_criteria`（**核心闸门仅人工可确认**）。
   本阶段禁止写任何业务代码、禁止创建/编辑 `feature_list.json`。
3. **实现编码（implementation）** —— 人工将 status 改为 `accepted` 后生效。
   - 人工执行 `uv run python scripts/feature_add.py`（dry-run 预览），
     确认后 `--yes` 把 `notes` 中的 feature 草案写入 `feature_list.json`；
   - Agent 按优先级逐条实现 feature 与对应单元测试；
   - 逐条验收：`uv run python scripts/verifier.py --feature-id <feat_id>`
     （verifier 执行 feature 的 `verification` 命令，通过才写入
     `status=passing`、`testedAt`、`evidence`；其余任何方式不得改 feature 状态）；
   - 全量门禁：`uv run pytest` + `uv run ruff check .` + `uv run pyright`。
4. **归档** —— 轮次验收后，把 `proposal.json` 归档到 `proposal_archive/`
   （命名：`proposal.<id>.<status>.<日期>.json`），并在新提案的 `history`
   字段追加该归档记录。

## feature_list.json 条目格式

```json
{
  "id": "feat_example",                          // feat_[a-z0-9_]+，全局唯一
  "priority": 1,                                  // 实现顺序
  "area": "common",                               // 模块归属
  "title": "功能标题",
  "user_visible_behavior": "用户可感知的行为描述",
  "verification": "uv run pytest tests/test_example.py -q",  // verifier 执行的单行命令
  "status": "not_started",                        // not_started / active / passing / blocked / waived
  "testedAt": null,
  "evidence": null,
  "history": []
}
```

> 条目位于文件顶层 `features` 数组内（整文件形如 `{"features": [...]}`）；手写 JSON 易错，推荐通过 `scripts/feature_add.py` 从提案草案导入。

## 开始新项目的清单

1. **项目认领**：`pyproject.toml` 改 `name` / `description` / `authors`（当前是脚手架作者的占位信息），然后 `uv lock` 同步锁文件（本项目为 uv 虚拟应用项目，`name` 仅作标识）；`src/main.py` 改 `APP_NAME`（测试自动跟随，无需改测试）；如需署名，同步改 `LICENSE` 的版权行；
2. **Git 归属**：二选一——保留脚手架历史（`git remote add origin <你的仓库>` 后推送，脚手架演化可追溯），或彻底切割（`rm -rf .git && git init` 从零开始）；
3. **工具链核对**：本机 uv 版本与 Dockerfile 固定版本（`ghcr.io/astral-sh/uv:0.13.6`）不一致时，二者取一对齐，并同步更新 `BOOTSTRAP_CONTRACT.md` 第 2 节；`[[tool.uv.index]]` 默认清华镜像，海外网络环境建议换回官方 PyPI；
4. 在 `proposal.json` 填写第一轮提案（模板内 `scaffold_note` 有逐步说明），`proposal_id` 换成实际 id；
5. 需要配置时：在 `.env.example` 补充配置键，本地复制为 `.env`（已入 `.gitignore` / `.dockerignore`）；
6. 新增依赖只由人工执行 `uv add` / `uv remove`，同步更新 `BOOTSTRAP_CONTRACT.md` 第 2 节；
7. 本 README 的脚手架说明换成新项目文档。

## 约束摘要（对 Agent）

- 所有命令统一 `uv run` 前缀；Agent 禁止执行 `init.sh`、`uv add/remove/venv/python install`
- `feature_list.json` 的 `status / testedAt / evidence` 只能由 `verifier.py` 写入
- `proposal.json` 的核心基线（gates、status）仅人工可改，Agent 只追加 explorations / spikes / notes
- 运行时依赖保持最小（当前仅 fastapi + uvicorn），`httpx2` 等仅限 dev/test
