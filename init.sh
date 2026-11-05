#!/usr/bin/env bash
set -euo pipefail

# ==============================================
# FastAPI Harness 项目初始化脚本
# 【重要】本脚本仅人工执行，OpenCode Agent禁止运行
# Agent 仅可读此脚本，用于了解项目环境与命令规范
# ==============================================

# 配置区
PY_VERSION="3.12"
VENV_DIR=".venv"

echo "===== Harness 项目初始化开始 ====="
echo "目标 Python 版本: ${PY_VERSION}"
echo "虚拟环境目录: ${VENV_DIR}"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先执行安装命令："
    echo 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    exit 1
fi

# 安装指定版本Python（uv会缓存，重复执行不会重复下载）
uv python install "${PY_VERSION}"

# 创建虚拟环境（不存在才创建）
if [ ! -d "${VENV_DIR}" ]; then
    uv venv --python "${PY_VERSION}" "${VENV_DIR}"
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在，跳过创建"
fi

# 同步依赖，读取 pyproject.toml + uv.lock
uv sync
echo "✅ 依赖同步完成"

echo ""
echo "===== 初始化完成，项目命令清单（给Agent阅读） ====="
echo "地基冒烟校验: uv run pytest tests/test_bootstrap_smoke.py"
echo "启动开发服务: uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
echo "Feature验收脚本: uv run python scripts/verifier.py --feature-id <feat_id>"
echo "单元测试: uv run pytest"
echo "代码检查: uv run ruff check src"
echo "类型检查: uv run pyright"
echo ""
echo "【Harness 约束摘要】"
echo "- Agent禁止执行 uv add / uv remove / uv venv / uv python install"
echo "- 新增依赖只输出清单，等待人工 uv add"
echo "- 禁止直接修改 feature_list.json 状态，状态仅 verifier.py 写入"
echo "=============================================="

