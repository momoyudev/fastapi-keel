# implementation-rules.md 编码实现阶段规则
> 仅在 bootstrap 地基就绪、proposal.json.status=accepted 且 feature_list.json 存在时加载生效

## 允许
1. 依照 feature_list 内每个feature的验收标准，按优先级实现业务代码、路由、业务单元测试
2. 调用 verifier 脚本验收feature：`uv run python scripts/verifier.py --feature-id <feat_id>`
3. 执行质量检查：`uv run pytest` / `uv run ruff check .` / `uv run pyright`
4. 启动开发服务用于接口验证：`uv run uvicorn src.main:app --reload`

## 禁止
1. 直接修改 feature_list.json 里 feature 的 status、testedAt；feature状态只能由 scripts/verifier.py 写入
2. 实现 proposal 中 out_of_scope 范围之外的功能
3. 直接执行 uv add / uv remove / uv venv / uv python install；依赖变更只输出清单，等待人工处理
4. 修改proposal.json核心基线内容

## 环境命令约定
- 所有命令统一使用 uv run 前缀
- init.sh 仅人工执行，Agent只允许读取，禁止执行
