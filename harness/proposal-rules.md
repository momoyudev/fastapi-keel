# proposal-rules.md 提案阶段规则
> 仅在 bootstrap 地基就绪、proposal.json 状态为 discussing / spike_required 时加载生效

## 允许
1. 针对当前需求做方案推演、exploration、风险分析、spike调研
2. 在 proposal.json 的 exploration / spikes / notes 字段追加内容
3. 识别需要新增依赖时，输出依赖名称+版本建议，提交给人工评审

## 禁止
1. 自行修改 proposal.json 的 status、goal、out_of_scope、final_selection 核心基线字段（仅人类可改）
2. 创建、编辑 feature_list.json
3. 编写业务实现代码、业务路由、业务单元测试
4. 提前固化 verifier 校验 shell 语句
5. 超出 proposal 约定 scope 设计方案

## 本阶段说明
本阶段只讨论方案，**不产出可运行业务代码**；无需执行业务相关测试、接口校验。
当人工将 proposal.json.status 修改为 accepted，本规则自动失效，切换到编码阶段规则。
