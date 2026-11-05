# bootstrap-rules.md 初始化阶段规则
> 本阶段是一次性前置地基搭建，地基就绪后不再进入本阶段

## 地基就绪判定标准
全部满足才算地基就绪：
1. 文件预检：BOOTSTRAP_CONTRACT.md、pyproject.toml、uv.lock 存在；src/ tests/ scripts/ harness/ 目录骨架齐全
2. 冒烟校验（仅校验底座样板，不校验业务代码）
   - uv run pytest tests/test_bootstrap_smoke.py 正常执行
   - uv run ruff check src 工具可调用
   - uv run pyright --help 无报错
   - uv run uvicorn src.main:app --help 可正常执行

校验触发时机：
- 全新仓库首次打开
- 人工修改 pyproject.toml / uv.lock、重建虚拟环境
- 执行命令时出现工具异常报错
日常反复讨论提案阶段，不再重复全套冒烟校验，复用就绪标记。

## 本阶段允许做
- 补齐目录骨架、创建样板文件
- 编写 tests/test_bootstrap_smoke.py、src/main.py 基础骨架
- 生成、更新 BOOTSTRAP_CONTRACT.md
- 修复工具链、骨架导入问题

## 本阶段禁止做
- 提案讨论、编辑 proposal.json、方案推演
- 编写任何业务接口、业务逻辑代码
- 新增 feature 条目到 feature_list.json

## BOOTSTRAP_CONTRACT.md 维护规则
BOOTSTRAP_CONTRACT.md 由 Agent 在初始化阶段生成、更新；
冒烟校验通过后Agent更新勾选状态，最终地基验收与Git checkpoint由人工完成。

BOOTSTRAP_CONTRACT.md 仅记录项目底座契约。
常规业务迭代（提案、编码、Feature验收）不更新本文件；
仅当底层环境、工具链、骨架目录、基础命令发生变更时，由Agent更新，人工复核固化。
本文件不跟踪业务Feature进度。

## 阶段退出条件
所有冒烟校验全部通过，更新 BOOTSTRAP_CONTRACT.md 清单，人工提交 Git checkpoint，地基标记就绪，退出初始化阶段。

