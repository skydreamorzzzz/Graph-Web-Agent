# 环境配置指南

## 快速开始

```bash
# 1. 安装依赖
pip install pyyaml playwright openai python-dotenv

# 2. 安装浏览器
playwright install chromium

# 3. 配置 API 密钥
echo "DEEPSEEK_API_KEY=sk-your-key" > .env

# 4. 测试
python scripts/test_llm.py

# 5. 运行
python scripts/run_experiment.py --benchmark miniwob --num-tasks 3
```

---

## API 配置

### DeepSeek（推荐）

**获取密钥**：https://platform.deepseek.com/

**配置**：
```bash
# 创建 .env 文件
echo "DEEPSEEK_API_KEY=sk-your-key" > .env
```

**成本**：¥1-2/百万tokens（约为 GPT-4 的 1/10）

**模型选择**：
```yaml
# config/default_params.yaml
router:
  small_model: "deepseek-chat"
  large_model: "deepseek-coder"
```

### 其他模型

**Qwen**：
```bash
QWEN_API_KEY=sk-your-key
```

**OpenAI**：
```bash
OPENAI_API_KEY=sk-your-key
```

---

## 依赖安装

```bash
# 核心依赖
pip install pyyaml playwright

# LLM 支持
pip install openai python-dotenv

# 可选：Qwen
pip install dashscope

# 可选：数据分析
pip install matplotlib numpy
```

---

## 测试配置

```bash
# 测试环境变量
python scripts/test_env.py

# 测试 LLM
python scripts/test_llm.py

# 测试系统
python scripts/test_system.py
```

---

## 故障排除

**环境变量未读取**：
```bash
# 方案1：当前会话设置
$env:DEEPSEEK_API_KEY = "sk-your-key"

# 方案2：使用 .env 文件
echo "DEEPSEEK_API_KEY=sk-your-key" > .env

# 方案3：重启 PowerShell
```

**API 认证失败**：
- 检查密钥是否正确
- 确认密钥未过期
- 检查网络连接

