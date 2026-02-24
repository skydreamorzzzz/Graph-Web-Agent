"""
Task Compiler - 将自然语言任务编译为结构化任务图
"""
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class NodeType(Enum):
    """任务节点类型"""
    NAVIGATE = "NAVIGATE"
    COLLECT = "COLLECT"
    EXTRACT = "EXTRACT"
    COMPUTE = "COMPUTE"
    ACT = "ACT"
    VERIFY = "VERIFY"
    ITERATE = "ITERATE"
    BRANCH = "BRANCH"


class TaskCompiler:
    """任务编译器 - 将自然语言转换为任务图"""
    
    def __init__(self, llm_client=None, config: Dict = None):
        self.llm_client = llm_client
        self.config = config or {}
        self.version = "1.0"
        
    def compile(self, task_description: str, task_id: str = None) -> Dict[str, Any]:
        """
        编译任务为结构化任务图
        
        Args:
            task_description: 自然语言任务描述
            task_id: 任务ID
            
        Returns:
            结构化任务图（JSON格式）
        """
        if not task_id:
            task_id = self._generate_task_id()
            
        # 使用LLM生成任务图
        task_graph = self._generate_graph_with_llm(task_description, task_id)
        
        # 如果LLM失败，使用保守模板
        if not task_graph:
            task_graph = self._fallback_template(task_description, task_id)
            
        return task_graph
    
    def _generate_graph_with_llm(self, task_description: str, task_id: str) -> Optional[Dict]:
        """使用LLM生成任务图"""
        if not self.llm_client:
            return None
            
        prompt = self._build_compilation_prompt(task_description)
        
        try:
            response = self.llm_client.generate(prompt)
            task_graph = self._parse_llm_response(response, task_id)
            return task_graph
        except Exception as e:
            print(f"LLM生成失败: {e}")
            return None
    
    def _build_compilation_prompt(self, task_description: str) -> str:
        """构建编译提示词"""
        return f"""你是一个Web任务编译器。将以下自然语言任务转换为结构化任务图。

任务描述: {task_description}

可用节点类型:
- NAVIGATE: 导航到URL
- COLLECT: 收集页面元素列表
- EXTRACT: 提取特定信息
- COMPUTE: 计算或处理数据
- ACT: 执行操作（点击、输入等）
- VERIFY: 验证状态
- ITERATE: 迭代处理
- BRANCH: 条件分支

输出JSON格式:
{{
  "nodes": [
    {{
      "id": "N1",
      "type": "NAVIGATE",
      "goal": "导航到搜索页面",
      "predicate": "URL包含/search",
      "idempotent": true,
      "params": {{"url": "https://example.com/search"}}
    }}
  ],
  "edges": [["N1", "N2"]]
}}

要求:
1. 图必须无环
2. 所有节点必须可达
3. 至少有一个终止节点
4. 节点ID格式: N1, N2, N3...

请输出任务图JSON:"""
    
    def _parse_llm_response(self, response: str, task_id: str) -> Dict:
        """解析LLM响应"""
        # 提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("无法从响应中提取JSON")
            
        graph_data = json.loads(json_match.group())
        
        # 添加元数据
        task_graph = {
            "task_id": task_id,
            "task_description": "",
            "nodes": graph_data.get("nodes", []),
            "edges": graph_data.get("edges", []),
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "compiler_version": self.version,
                "estimated_steps": len(graph_data.get("nodes", []))
            }
        }
        
        return task_graph
    
    def _fallback_template(self, task_description: str, task_id: str) -> Dict:
        """保守模板 - 当LLM失败时使用"""
        return {
            "task_id": task_id,
            "task_description": task_description,
            "nodes": [
                {
                    "id": "N1",
                    "type": "NAVIGATE",
                    "goal": "导航到起始页面",
                    "predicate": "页面加载完成",
                    "idempotent": True,
                    "params": {}
                },
                {
                    "id": "N2",
                    "type": "EXTRACT",
                    "goal": "提取页面信息",
                    "predicate": "信息提取完成",
                    "idempotent": True,
                    "params": {},
                    "control_flow": None  # 用于ITERATE/BRANCH的控制流信息
                }
            ],
            "edges": [["N1", "N2"]],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "compiler_version": self.version,
                "estimated_steps": 2,
                "fallback": True
            }
        }
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"task_{timestamp}"


class LLMClient:
    """LLM客户端接口（需要根据实际使用的LLM实现）"""
    
    def __init__(self, model_name: str = "gpt-4", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key
        
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成响应
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM响应文本
        """
        # TODO: 实现实际的LLM调用
        # 这里需要根据使用的LLM（OpenAI, Anthropic等）实现
        raise NotImplementedError("需要实现具体的LLM调用逻辑")


