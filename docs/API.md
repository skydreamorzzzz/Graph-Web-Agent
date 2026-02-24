# API 参考

## 核心模块

### TaskCompiler

```python
from task_compiler.compiler import TaskCompiler

compiler = TaskCompiler(llm_client=llm_client)
task_graph = compiler.compile("搜索GitHub上的playwright项目")
```

### GraphExecutor

```python
from graph_executor.executor import GraphExecutor

executor = GraphExecutor(browser_env, verifier, router, rollback_manager)
result = executor.execute(task_graph)
```

### LocalRepairEngine

```python
from local_repair.repair import LocalRepairEngine

repair_engine = LocalRepairEngine()
failure_type = repair_engine.classify_failure(node, verification, page_state)
strategy = repair_engine.select_repair_strategy(failure_type, attempt=0)
```

### CostAwareRouter

```python
from router.router import CostAwareRouter

router = CostAwareRouter(config)
model_tier = router.route(node, page_state, context)
```

---

## 任务图格式

```json
{
  "task_id": "task_001",
  "nodes": [
    {
      "id": "N1",
      "type": "NAVIGATE",
      "goal": "导航到搜索页面",
      "predicate": "URL包含/search",
      "idempotent": true,
      "params": {"url": "https://example.com"}
    }
  ],
  "edges": [["N1", "N2"]],
  "metadata": {
    "created_at": "2024-01-01T00:00:00",
    "estimated_steps": 5
  }
}
```

---

## 节点类型

- **NAVIGATE**: 页面导航
- **COLLECT**: 收集元素列表
- **EXTRACT**: 提取结构化信息
- **COMPUTE**: 数据处理
- **ACT**: 执行操作（点击、输入等）
- **VERIFY**: 验证状态
- **ITERATE**: 循环处理
- **BRANCH**: 条件分支

---

## 配置结构

```python
config = {
    "system": {
        "max_steps": 100,
        "max_repair_per_node": 3
    },
    "verification": {
        "confidence_threshold": 0.7,
        "hard_check_weight": 0.6,
        "soft_check_weight": 0.3,
        "consistency_weight": 0.1
    },
    "router": {
        "small_model": "deepseek-chat",
        "large_model": "deepseek-coder",
        "upgrade_after_failures": 3
    }
}
```

