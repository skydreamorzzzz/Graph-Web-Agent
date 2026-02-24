# Graph-Compiled Web Agent

基于任务图编译、局部修复和成本感知路由的结构化 Web Agent 研究项目。

## 核心创新

1. **Task Graph Compilation** - 任务图编译
2. **Dual-path Verification** - 双路验证（Hard + Soft + Consistency）
3. **Local Repair Engine** - 失败驱动的局部修复
4. **Cost-aware Routing** - 成本感知路由

## 快速开始

### 1. 安装依赖

```bash
pip install pyyaml playwright openai python-dotenv
playwright install chromium
```

### 2. 配置 API 密钥

```bash
# 创建 .env 文件
echo "DEEPSEEK_API_KEY=sk-your-key" > .env
```

获取密钥：https://platform.deepseek.com/

### 3. 测试

```bash
# 测试配置
python scripts/test_llm.py

# 快速测试（3个任务）
python scripts/run_experiment.py --benchmark miniwob --num-tasks 3
```

### 4. 运行实验

```bash
# 完整实验（30个任务）
python scripts/run_experiment.py --benchmark miniwob --num-tasks 30

# 分析结果
python scripts/analyze_results.py
```

---

## 系统架构

```
Layer 1: Task Compiler
  └─ 自然语言 → 结构化任务图（8种节点类型）

Layer 2: Graph Executor
  └─ 拓扑排序执行 + WAIT_UNTIL 机制

Layer 3: Dual Verification
  └─ Hard Check + Soft Check + Consistency → 置信度

Layer 4: Local Repair
  └─ 失败分类 → 修复策略 → 最小回滚子图
```

---

## 项目结构

```
Graph-Web-Agent/
├── config/              # 配置文件
├── data/                # 数据集
├── docs/                # 文档
│   ├── SETUP.md        # 环境配置
│   ├── USAGE.md        # 使用指南
│   ├── METHOD.md       # 方法论
│   └── API.md          # API 参考
├── src/                 # 源代码
│   ├── task_compiler/   # 任务编译器
│   ├── graph_executor/  # 图执行器
│   ├── local_repair/    # 局部修复引擎
│   ├── router/          # 成本路由器
│   ├── models/          # 模型和浏览器环境
│   └── utils/           # 工具函数
├── results/             # 实验结果
└── scripts/             # 运行脚本
```

---

## 配置说明

### 系统参数（config/default_params.yaml）

```yaml
system:
  max_steps: 100
  max_repair_per_node: 3

verification:
  confidence_threshold: 0.7

router:
  small_model: "deepseek-chat"
  large_model: "deepseek-coder"
```

### 实验参数（config/experiment_params.yaml）

```yaml
experiment:
  name: "baseline_experiment"
  benchmark: "miniwob"
  num_tasks: 30
```

---

## 使用示例

### 编译任务图

```python
from task_compiler.compiler import TaskCompiler

compiler = TaskCompiler(llm_client=llm_client)
task_graph = compiler.compile("搜索GitHub上的playwright项目")
```

### 执行任务

```python
from graph_executor.executor import GraphExecutor

executor = GraphExecutor(browser_env, verifier, router, rollback_manager)
result = executor.execute(task_graph)
```

### 局部修复

```python
from local_repair.repair import LocalRepairEngine

repair_engine = LocalRepairEngine()
failure_type = repair_engine.classify_failure(node, verification, page_state)
strategy = repair_engine.select_repair_strategy(failure_type, attempt=0)
```

---

## 评估指标

- **Success Rate** - 成功率
- **Avg Steps** - 平均步数
- **LLM Calls** - LLM 调用次数
- **Cost per Success** - 每次成功成本
- **Repair Depth** - 修复深度
- **Failure Distribution** - 失败分布

---

## 开发阶段

### Phase 1 ✅
- 任务编译器
- 图验证器
- 图执行器
- 双路验证器

### Phase 2 ✅
- 局部修复引擎
- 回滚管理器
- 成本路由器

### Phase 3 ⏳
- 完整实验（100任务）
- 成功率-成本曲线
- 论文撰写

---

## 文档

- [环境配置](docs/SETUP.md) - 安装和配置指南
- [使用指南](docs/USAGE.md) - 运行实验和分析结果
- [方法论](docs/METHOD.md) - 核心创新和系统架构
- [API 参考](docs/API.md) - 模块和接口文档

---

## 许可证

MIT License

---

## 引用

```bibtex
@article{graph-web-agent-2026,
  title={Graph-Compiled Web Agent with Local Repair and Cost-Aware Routing},
  author={Your Name},
  year={2026}
}
```
