# AGENTS.md - Harness 根调度文件
## 全局通用（永久生效）
1. 所有基线文件（proposal.json、feature_list.json）的核心闸门、验收标准，仅人类可以修改基线定义。
2. 你不能自行放宽约束、修改验收标准、篡改状态字段（status / testedAt）。
3. 任何输出必须明确标注假设、未知项、风险，禁止无前提的确定性承诺。
4. 读取子规则文件后，子规则优先级高于本文件的简要描述。

## 阶段路由逻辑（自动判断）
读取项目根文件：
0. 先检查 Bootstrap 地基就绪状态
   - 地基未就绪 →【Bootstrap初始化阶段】，加载 `harness/bootstrap-rules.md`；
   - 地基就绪，才继续往下路由到业务阶段。
1. 若存在 `proposal.json`，且 status in ["discussing", "spike_required"]
   → 当前为【提案阶段】，加载 `harness/proposal-rules.md`，严格遵循提案Harness；
   → 禁止创建、编辑 feature_list.json，禁止编写业务实现代码、固化shell校验语句。
2. 若 `proposal.json` status = "accepted" 且存在 feature_list.json
   → 当前为【实现编码阶段】，加载 `harness/implementation-rules.md`；
   → 提案规则不再生效，进入feature_list + verifier 闭环流程。
3. 若两个文件都不存在、且地基已经就绪：进入自由探索模式，但依然遵守全局护栏。

## 文件读取约定
你具备读取项目内本地markdown规则文件的能力；
不要把所有规则记忆在上下文中，需要时读取对应规则文件作为当前阶段的约束源。
你不需要复述全部规则，只需在行动时遵守；需要确认约束时再查阅对应小节。

