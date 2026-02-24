# 使用指南

## 快速运行

```bash
# 单个任务测试
python scripts/run_experiment.py --task "导航到Google"

# MiniWoB++ 测试（3个任务）
python scripts/run_experiment.py --benchmark miniwob --num-tasks 3

# 完整实验（30个任务）
python scripts/run_experiment.py --benchmark miniwob --num-tasks 30
```

---

## 数据集

### MiniWoB++（推荐用于开发）

**特点**：
- 100+ 简单任务
- 每个任务 10-30 秒
- 本地运行，快速迭代

**使用**：
```bash
python scripts/run_experiment.py --benchmark miniwob --num-tasks 10
```

### WebArena（用于最终评估）

**特点**：
- 812 个复杂任务
- 真实网站环境
- 每个任务 1-5 分钟

**使用**：
```bash
python scripts/run_experiment.py --benchmark webarena --num-tasks 30
```

---

## 配置参数

### 系统参数（config/default_params.yaml）

```yaml
system:
  max_steps: 100                    # 最大执行步数
  max_repair_per_node: 3            # 每节点最大修复次数

verification:
  confidence_threshold: 0.7         # 验证阈值

router:
  small_model: "deepseek-chat"      # 小模型
  large_model: "deepseek-coder"     # 大模型
  upgrade_after_failures: 3         # 失败后升级阈值
```

### 实验参数（config/experiment_params.yaml）

```yaml
experiment:
  name: "baseline_experiment"
  benchmark: "miniwob"
  num_tasks: 30
```

---

## 结果分析

### 查看结果

```bash
# 日志目录
results/logs/

# 任务图
results/task_graphs/

# 性能指标
results/performance/
```

### 分析脚本

```bash
# 分析结果
python scripts/analyze_results.py

# 对比实验
python scripts/compare_experiments.py
```

---

## 开发流程

### 阶段1：快速验证（1-2天）
```bash
python scripts/run_experiment.py --benchmark miniwob --num-tasks 10
```

### 阶段2：完整测试（3-5天）
```bash
python scripts/run_experiment.py --benchmark miniwob --num-tasks 100
```

### 阶段3：真实评估（1-2周）
```bash
python scripts/run_experiment.py --benchmark webarena --num-tasks 30
```

---

## 命令参考

```bash
# 指定配置文件
python scripts/run_experiment.py --config config/custom.yaml

# 禁用修复机制
python scripts/run_experiment.py --no-repair

# 指定实验配置
python scripts/run_experiment.py --experiment config/experiment_params.yaml
```

