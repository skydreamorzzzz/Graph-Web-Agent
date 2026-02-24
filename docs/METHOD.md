# 方法论

## 核心创新

### 1. 任务图编译
将自然语言任务编译为结构化 DAG，支持 8 种节点类型和运行时动态展开。

### 2. 双路验证
- **Hard Check**：结构验证（URL、DOM、标题）
- **Soft Check**：语义验证（LLM 判断）
- **Consistency Check**：一致性验证（字段完整性）

### 3. 局部修复
- 5 种失败类型分类
- 修复策略表
- 最小回滚子图算法

### 4. 成本感知路由
- NO_LLM：规则解析
- SMALL：小模型（deepseek-chat）
- LARGE：大模型（deepseek-coder）

---

## 系统架构

```
Layer 1: Task Compiler
  └─ 自然语言 → 结构化任务图

Layer 2: Graph Executor
  └─ 拓扑排序执行 + WAIT_UNTIL 机制

Layer 3: Dual Verification
  └─ Hard + Soft + Consistency → 置信度

Layer 4: Local Repair
  └─ 失败分类 → 修复策略 → 最小回滚
```

---

## 失败类型与修复策略

| 失败类型 | 修复策略 | 回滚深度 |
|---------|---------|---------|
| GROUNDING_FAIL | 切换锚点 / 等待元素 | 0 |
| STATE_FAIL | 关闭弹窗 / 重新导航 | 0-1 |
| EXTRACTION_FAIL | 扩展页面 / 调整规则 | 0 |
| COMPUTE_FAIL | 代码反思 | 0 |
| PLAN_FAIL | 回滚至 COLLECT | 2 |

---

## 评估指标

- **Success Rate**：成功率
- **Avg Steps**：平均步数
- **LLM Calls**：LLM 调用次数
- **Cost per Success**：每次成功成本
- **Repair Depth**：修复深度

---

## 研究价值

探索结构化编译是否优于黑箱决策，局部修复是否比全局重规划更高效。

