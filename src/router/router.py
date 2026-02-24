"""
Cost-aware Router - 成本感知路由器
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ModelTier(Enum):
    """模型层级"""
    NO_LLM = "no_llm"  # 不使用LLM，直接DOM解析
    SMALL = "small"  # 小模型（如gpt-3.5-turbo）
    LARGE = "large"  # 大模型（如gpt-4）


@dataclass
class CostStats:
    """成本统计"""
    total_calls: int = 0
    no_llm_calls: int = 0
    small_model_calls: int = 0
    large_model_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    calls_by_node: Dict[str, int] = field(default_factory=dict)


class CostAwareRouter:
    """成本感知路由器"""
    
    # 模型价格（每1K tokens，美元）
    MODEL_PRICES = {
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03}
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.small_model = self.config.get("small_model", "gpt-3.5-turbo")
        self.large_model = self.config.get("large_model", "gpt-4")
        self.upgrade_threshold = self.config.get("upgrade_after_failures", 3)
        self.dom_complexity_threshold = self.config.get("use_llm_threshold", 0.5)
        
        # 统计信息
        self.stats = CostStats()
        self.failure_counts: Dict[str, int] = {}
        
    def route(
        self,
        node: Dict,
        page_state: Dict,
        context: Dict = None
    ) -> ModelTier:
        """
        路由决策：选择使用哪个模型层级
        
        Args:
            node: 当前节点
            page_state: 页面状态
            context: 执行上下文
            
        Returns:
            模型层级
        """
        node_id = node.get("id")
        node_type = node.get("type")
        
        # 规则1: DOM可直接解析的节点不使用LLM
        if self._can_parse_directly(node, page_state):
            self.stats.no_llm_calls += 1
            return ModelTier.NO_LLM
        
        # 规则2: 检查该节点的失败次数
        failure_count = self.failure_counts.get(node_id, 0)
        if failure_count >= self.upgrade_threshold:
            # 升级到大模型
            self.stats.large_model_calls += 1
            return ModelTier.LARGE
        
        # 规则3: 评估DOM复杂度
        complexity = self._evaluate_dom_complexity(page_state)
        if complexity > self.dom_complexity_threshold:
            # 复杂页面使用大模型
            self.stats.large_model_calls += 1
            return ModelTier.LARGE
        
        # 规则4: 某些节点类型优先使用小模型
        if node_type in ["VERIFY", "EXTRACT"]:
            self.stats.small_model_calls += 1
            return ModelTier.SMALL
        
        # 默认使用小模型
        self.stats.small_model_calls += 1
        return ModelTier.SMALL
    
    def record_failure(self, node_id: str) -> None:
        """记录节点失败"""
        if node_id not in self.failure_counts:
            self.failure_counts[node_id] = 0
        self.failure_counts[node_id] += 1
    
    def record_success(self, node_id: str) -> None:
        """记录节点成功（重置失败计数）"""
        if node_id in self.failure_counts:
            self.failure_counts[node_id] = 0
    
    def record_call(
        self,
        model_tier: ModelTier,
        node_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> None:
        """
        记录LLM调用
        
        Args:
            model_tier: 模型层级
            node_id: 节点ID
            input_tokens: 输入token数
            output_tokens: 输出token数
        """
        self.stats.total_calls += 1
        
        # 记录每个节点的调用次数
        if node_id not in self.stats.calls_by_node:
            self.stats.calls_by_node[node_id] = 0
        self.stats.calls_by_node[node_id] += 1
        
        # 计算成本
        if model_tier == ModelTier.SMALL:
            model_name = self.small_model
        elif model_tier == ModelTier.LARGE:
            model_name = self.large_model
        else:
            return
        
        if model_name in self.MODEL_PRICES:
            prices = self.MODEL_PRICES[model_name]
            cost = (input_tokens / 1000 * prices["input"] + 
                   output_tokens / 1000 * prices["output"])
            
            self.stats.total_tokens += (input_tokens + output_tokens)
            self.stats.total_cost += cost
    
    def get_model_name(self, model_tier: ModelTier) -> Optional[str]:
        """获取模型名称"""
        if model_tier == ModelTier.NO_LLM:
            return None
        elif model_tier == ModelTier.SMALL:
            return self.small_model
        elif model_tier == ModelTier.LARGE:
            return self.large_model
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_calls": self.stats.total_calls,
            "no_llm_calls": self.stats.no_llm_calls,
            "small_model_calls": self.stats.small_model_calls,
            "large_model_calls": self.stats.large_model_calls,
            "total_tokens": self.stats.total_tokens,
            "total_cost": self.stats.total_cost,
            "cost_per_call": (
                self.stats.total_cost / self.stats.total_calls 
                if self.stats.total_calls > 0 else 0
            ),
            "calls_by_node": self.stats.calls_by_node
        }
    
    def _can_parse_directly(self, node: Dict, page_state: Dict) -> bool:
        """
        判断是否可以直接解析（不需要LLM）
        
        Returns:
            True表示可以直接解析
        """
        node_type = node.get("type")
        params = node.get("params", {})
        
        # NAVIGATE节点如果有明确URL，不需要LLM
        if node_type == "NAVIGATE" and params.get("url"):
            return True
        
        # COLLECT节点如果有明确selector，不需要LLM
        if node_type == "COLLECT" and params.get("selector"):
            return True
        
        # EXTRACT节点如果有明确字段定义，可能不需要LLM
        if node_type == "EXTRACT":
            fields = params.get("fields", [])
            # 如果所有字段都有selector，不需要LLM
            if all(isinstance(f, dict) and "selector" in f for f in fields):
                return True
        
        # ACT节点如果有明确target，不需要LLM
        if node_type == "ACT" and params.get("target"):
            return True
        
        return False
    
    def _evaluate_dom_complexity(self, page_state: Dict) -> float:
        """
        评估DOM复杂度
        
        Returns:
            复杂度分数 [0, 1]
        """
        dom_elements = page_state.get("dom_elements", [])
        text_content = page_state.get("text_content", "")
        
        # 简单的复杂度评估
        element_count = len(dom_elements)
        text_length = len(text_content)
        
        # 归一化
        element_score = min(element_count / 1000, 1.0)  # 假设1000个元素为高复杂度
        text_score = min(text_length / 10000, 1.0)  # 假设10000字符为高复杂度
        
        # 综合评分
        complexity = (element_score + text_score) / 2
        
        return complexity
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = CostStats()
        self.failure_counts.clear()

