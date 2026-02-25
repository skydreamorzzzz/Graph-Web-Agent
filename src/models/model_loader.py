"""
Model Loader - 支持多种LLM提供商
"""
import os
from typing import Dict, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - graceful fallback when optional dependency is missing
    load_dotenv = None


class ModelLoader:
    """模型加载器 - 支持OpenAI、Anthropic、DeepSeek、Qwen等"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # 先尝试从 .env 文件加载（如果存在）
        if load_dotenv:
            load_dotenv()
        
        # 获取API密钥（优先级：环境变量 > .env文件 > config）
        self.openai_api_key = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or self.config.get("openai_api_key")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or self.config.get("anthropic_api_key")
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or self.config.get("deepseek_api_key")
        self.qwen_api_key = (os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") or 
                            os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or 
                            self.config.get("qwen_api_key"))
        
    def load_model(self, model_name: str):
        """
        加载指定模型
        
        支持的模型：
        - OpenAI: gpt-3.5-turbo, gpt-4, gpt-4-turbo
        - Anthropic: claude-3-sonnet, claude-3-opus
        - DeepSeek: deepseek-chat, deepseek-coder
        - Qwen: qwen-turbo, qwen-plus, qwen-max
        """
        if model_name.startswith("gpt"):
            return self._load_openai_model(model_name)
        elif model_name.startswith("claude"):
            return self._load_anthropic_model(model_name)
        elif model_name.startswith("deepseek"):
            return self._load_deepseek_model(model_name)
        elif model_name.startswith("qwen"):
            return self._load_qwen_model(model_name)
        else:
            # 使用Mock模型
            print(f"警告: 未知模型 {model_name}，使用Mock模式")
            return MockLLM(model_name)
    
    def _load_openai_model(self, model_name: str):
        """加载OpenAI模型"""
        if not self.openai_api_key:
            print("警告: OpenAI API密钥未配置，使用Mock模式")
            return MockLLM(model_name)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            return OpenAILLM(client, model_name)
        except ImportError:
            print("警告: openai包未安装")
            return MockLLM(model_name)
    
    def _load_anthropic_model(self, model_name: str):
        """加载Anthropic模型"""
        if not self.anthropic_api_key:
            print("警告: Anthropic API密钥未配置，使用Mock模式")
            return MockLLM(model_name)
        
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self.anthropic_api_key)
            return AnthropicLLM(client, model_name)
        except ImportError:
            print("警告: anthropic包未安装")
            return MockLLM(model_name)
    
    def _load_deepseek_model(self, model_name: str):
        """加载DeepSeek模型"""
        if not self.deepseek_api_key:
            print("警告: DeepSeek API密钥未配置，使用Mock模式")
            return MockLLM(model_name)
        
        try:
            from openai import OpenAI
            # DeepSeek使用OpenAI兼容接口
            client = OpenAI(
                api_key=self.deepseek_api_key,
                base_url="https://api.deepseek.com"
            )
            return DeepSeekLLM(client, model_name)
        except ImportError:
            print("警告: openai包未安装（DeepSeek需要）")
            return MockLLM(model_name)
    
    def _load_qwen_model(self, model_name: str):
        """加载Qwen模型"""
        if not self.qwen_api_key:
            print("警告: Qwen API密钥未配置，使用Mock模式")
            return MockLLM(model_name)
        
        try:
            # 尝试使用DashScope SDK
            import dashscope
            dashscope.api_key = self.qwen_api_key
            return QwenLLM(model_name, self.qwen_api_key)
        except ImportError:
            print("警告: dashscope包未安装，尝试使用OpenAI兼容接口")
            try:
                from openai import OpenAI
                # Qwen也支持OpenAI兼容接口
                client = OpenAI(
                    api_key=self.qwen_api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                return QwenCompatibleLLM(client, model_name)
            except ImportError:
                print("警告: openai包未安装")
                return MockLLM(model_name)


class OpenAILLM:
    """OpenAI LLM封装"""
    
    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name
    
    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        """生成响应"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=kwargs.get("temperature", 0.1)
        )
        return response.choices[0].message.content


class AnthropicLLM:
    """Anthropic LLM封装"""
    
    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name
    
    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        """生成响应"""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


class DeepSeekLLM:
    """DeepSeek LLM封装（使用OpenAI兼容接口）"""
    
    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name
        print(f"[OK] DeepSeek模型已加载: {model_name}")
    
    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        """生成响应"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=kwargs.get("temperature", 0.1),
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            raise


class QwenLLM:
    """Qwen LLM封装（使用DashScope SDK）"""
    
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
        print(f"[OK] Qwen模型已加载: {model_name}")
    
    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        """生成响应"""
        try:
            import dashscope
            from dashscope import Generation
            
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=kwargs.get("temperature", 0.1),
                result_format='message'
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"Qwen API错误: {response.message}")
        except Exception as e:
            print(f"Qwen API调用失败: {e}")
            raise


class QwenCompatibleLLM:
    """Qwen LLM封装（使用OpenAI兼容接口）"""
    
    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name
        print(f"[OK] Qwen模型已加载（兼容模式）: {model_name}")
    
    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        """生成响应"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=kwargs.get("temperature", 0.1)
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Qwen API调用失败: {e}")
            raise


class MockLLM:
    """Mock LLM（用于测试）"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        print(f"[MOCK] 使用Mock模式: {model_name}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """返回Mock响应"""
        # 返回一个简单的任务图JSON
        return '''
{
  "nodes": [
    {
      "id": "N1",
      "type": "NAVIGATE",
      "goal": "导航到起始页面",
      "predicate": "页面加载完成",
      "idempotent": true,
      "params": {}
    },
    {
      "id": "N2",
      "type": "EXTRACT",
      "goal": "提取页面信息",
      "predicate": "信息提取完成",
      "idempotent": true,
      "params": {}
    }
  ],
  "edges": [["N1", "N2"]]
}
'''
