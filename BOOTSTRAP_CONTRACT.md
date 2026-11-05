# BOOTSTRAP_CONTRACT.md 地基契约

> 本文件仅记录项目**底座契约**（环境、工具链、骨架目录、基础命令）。
> 常规业务迭代（提案、编码、Feature 验收）不更新本文件；不跟踪业务 Feature 进度。
> 仅当底层环境、工具链、骨架目录、基础命令发生变更时，由 Agent 更新，人工复核固化。

## 1. 文件预检

| 项 | 要求 | 状态 |
|---|---|---|
| `BOOTSTRAP_CONTRACT.md` | 存在（本文件） | [x] |
| `pyproject.toml` | 存在，声明 `requires-python` 与依赖 | [x] |
| `uv.lock` | 存在，锁定依赖版本 | [x] |
| `AGENTS.md` / `harness/` | 流程规则齐全：AGENTS.md 阶段路由 + harness/ 下 proposal / implementation / bootstrap 规则文件 | [x] |
| `src/` | 目录骨架存在，含 `src/main.py`（仅实例化 app，无业务路由）与 `src/logging_config.py`（地基日志） | [x] |
| `tests/` | 目录骨架存在，含 `tests/test_bootstrap_smoke.py`、`tests/test_log_format.py`（地基日志测试） | [x] |
| `scripts/` | 目录骨架存在，含 `scripts/verifier.py`、`scripts/feature_add.py` | [x] |
| `proposal.json` | 存在，为空白提案模板（status=discussing，gates 留占位说明；首轮提案时填写） | [x] |
| `feature_list.json` | 存在，`features` 为空数组；条目由 `scripts/feature_add.py` 追加、状态仅由 `scripts/verifier.py` 写入 | [x] |
| `.env.example` | 存在（配置键模板）；`.env` 不得提交、不得进镜像 | [x] |
| `proposal_archive/` | 存在（空目录，`.gitkeep` 占位）；已验收提案按惯例归档于此 | [x] |

## 2. 环境与工具链版本（校验时实际值）

| 项 | 版本 |
|---|---|
| Python | 3.12.16（`requires-python = ">=3.12"`） |
| uv | 0.13.6 |
| 虚拟环境 | `.venv`（由 `init.sh` 创建，Agent 不执行 `uv venv` / `uv python install`） |
| FastAPI | 0.162.0 |
| Uvicorn | 0.54.0 |
| pytest | 9.2.0 |
| ruff | 0.17.3 |
| pyright | 1.1.414 |
| httpx2 | 2.16.0（**仅 dev/test**，供 starlette TestClient 使用，不进运行时） |
| 运行时依赖 | 仅 `fastapi>=0.162.0`、`uvicorn>=0.54.0` 两项 |
| 包索引 | `https://pypi.tuna.tsinghua.edu.cn/simple`（默认源） |

依赖变更只由人工执行 `uv add` / `uv remove`；Agent 仅输出依赖清单。

## 3. 冒烟校验（仅校验底座样板，不校验业务代码）

| 命令 | 期望 | 结果 |
|---|---|---|
| `uv run pytest tests/test_bootstrap_smoke.py` | 正常执行，2 passed | [x] 2 passed in 0.26s |
| `uv run ruff check src` | 工具可调用 | [x] All checks passed! |
| `uv run pyright --help` | 无报错 | [x] 正常输出 Usage |
| `uv run uvicorn src.main:app --help` | 可正常执行 | [x] 正常输出 Usage |

校验时间：2026-11-04

## 4. 基础命令清单

```bash
uv run pytest tests/test_bootstrap_smoke.py        # 地基冒烟校验
uv run pytest                                      # 全部单元测试
uv run ruff check src                              # 代码检查
uv run pyright                                     # 类型检查
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload   # 启动开发服务（0.0.0.0 为刻意选择，便于局域网手工测试）
uv run python scripts/verifier.py --feature-id <feat_id>   # Feature 验收（编码阶段）
uv run python scripts/feature_add.py                       # 从 proposal.json 草案导入 feature（dry-run 预览）
uv run python scripts/feature_add.py --yes                 # 确认写入 feature_list.json（仅人工执行）
init.sh                                            # 仅人工执行，Agent 禁止运行
```

## 5. 阶段退出条件

- [x] 所有冒烟校验通过（见第 3 节）
- [x] 人工提交 Git checkpoint
- [x] 地基标记就绪，退出初始化阶段

> 说明：地基已由人工复核并标记就绪（见第 6 节模板基线记录）。
> 脚手架重置（业务代码清空、基线恢复空白模板）不影响地基就绪状态。

## 6. 变更记录

| 日期 | 触发 | 变更 | 冒烟重校验 | 人工复核 |
|---|---|---|---|---|
| 2026-11-05 | 模板基线 v0.1.0 | 地基基线定稿（本地时区日志、Docker TZ、uv 虚拟项目、脚手架命名）；历史明细见 `CHANGELOG.md` | ✅ pytest 6 passed、ruff check . All checks passed、pyright 0 errors、Docker 构建/运行通过 | [x] |

> 变更依据：`bootstrap-rules.md`「校验触发时机 —— 人工修改 pyproject.toml / uv.lock」及人工明确指令。
