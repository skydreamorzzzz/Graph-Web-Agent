"""
Dual-path Verification - 双路验证机制
"""
from typing import Dict, Any, Tuple
from dataclasses import dataclass
import re


@dataclass
class VerificationResult:
    """验证结果"""
    confidence: float  # 总置信度 [0, 1]
    hard_score: float  # 硬验证分数
    soft_score: float  # 软验证分数
    consistency_score: float  # 一致性分数
    passed: bool  # 是否通过
    details: Dict[str, Any]  # 详细信息
    
    def to_dict(self):
        """转换为字典（用于JSON序列化）"""
        return {
            "confidence": self.confidence,
            "hard_score": self.hard_score,
            "soft_score": self.soft_score,
            "consistency_score": self.consistency_score,
            "passed": self.passed,
            "details": self.details
        }


class DualVerifier:
    """双路验证器"""
    
    def __init__(self, config: Dict = None, llm_client=None):
        self.config = config or {}
        self.llm_client = llm_client
        
        # 权重配置
        self.w_hard = self.config.get("hard_check_weight", 0.6)
        self.w_soft = self.config.get("soft_check_weight", 0.3)
        self.w_consistency = self.config.get("consistency_weight", 0.1)
        self.threshold = self.config.get("confidence_threshold", 0.7)
        
    def verify(self, node: Dict, page_state: Dict, model_tier=None) -> VerificationResult:
        """
        验证节点执行结果
        
        Args:
            node: 任务节点
            page_state: 当前页面状态（包含URL、DOM、截图等）
            
        Returns:
            验证结果
        """
        node_type = node.get("type")
        
        # 1. 硬验证（结构验证）
        hard_score = self._hard_check(node, page_state)
        
        # 2. 软验证（语义验证）- 根据路由决策选择是否使用LLM
        if model_tier and hasattr(model_tier, 'value') and model_tier.value == "no_llm":
            soft_score = 0.0  # 不使用LLM时软验证分数为0
        else:
            soft_score = self._soft_check(node, page_state)
        
        # 3. 一致性验证
        consistency_score = self._consistency_check(node, page_state)
        
        # 计算总置信度
        confidence = (
            self.w_hard * hard_score +
            self.w_soft * soft_score +
            self.w_consistency * consistency_score
        )
        
        passed = confidence >= self.threshold
        
        return VerificationResult(
            confidence=confidence,
            hard_score=hard_score,
            soft_score=soft_score,
            consistency_score=consistency_score,
            passed=passed,
            details={
                "node_id": node.get("id"),
                "node_type": node_type,
                "threshold": self.threshold
            }
        )
    
    def _hard_check(self, node: Dict, page_state: Dict) -> float:
        """
        硬验证 - 结构验证
        
        检查项:
        - URL pattern
        - DOM关键元素存在
        - a11y-tree signature
        - 页面标题匹配
        
        Returns:
            分数 [0, 0.6]
        """
        score = 0.0
        max_score = 0.6
        node_type = node.get("type")
        predicate = node.get("predicate", "")
        
        current_url = page_state.get("url", "")
        page_title = page_state.get("title", "")
        dom_elements = page_state.get("dom_elements", [])
        
        # URL检查 (0.2分)
        if self._check_url_pattern(predicate, current_url):
            score += 0.2
            
        # 页面标题检查 (0.15分)
        if self._check_title_match(predicate, page_title):
            score += 0.15
            
        # DOM元素检查 (0.15分)
        if self._check_dom_elements(node, dom_elements):
            score += 0.15
            
        # 节点类型特定检查 (0.1分)
        if node_type == "NAVIGATE":
            if current_url and current_url != "about:blank":
                score += 0.1
        elif node_type == "COLLECT":
            if len(dom_elements) > 0:
                score += 0.1
        elif node_type == "EXTRACT":
            if page_state.get("extracted_data"):
                score += 0.1
        elif node_type == "ACT":
            # 检查操作是否改变了页面状态
            if page_state.get("state_changed", False):
                score += 0.1
                
        return min(score, max_score)
    
    def _soft_check(self, node: Dict, page_state: Dict) -> float:
        """
        软验证 - 语义验证
        
        使用廉价模型判断: "当前页面是否满足目标状态？"
        
        Returns:
            分数 [0, 0.3]
        """
        if not self.llm_client:
            # 如果没有LLM，使用简单的关键词匹配
            return self._simple_semantic_check(node, page_state)
            
        goal = node.get("goal", "")
        page_content = page_state.get("text_content", "")
        
        prompt = f"""判断当前页面状态是否满足目标。

目标: {goal}
当前页面内容摘要: {page_content[:500]}...

请回答: 是否满足目标？(是/否)
置信度: (0-100)

格式: 是/否, 置信度"""

        try:
            response = self.llm_client.generate(prompt, max_tokens=50)
            confidence = self._parse_soft_check_response(response)
            return confidence * 0.3  # 最大0.3分
        except Exception as e:
            print(f"软验证失败: {e}")
            return 0.0
    
    def _consistency_check(self, node: Dict, page_state: Dict) -> float:
        """
        一致性检查
        
        检查项:
        - EXTRACT: 字段齐全率
        - COLLECT: 数量 > 0
        - COMPUTE: 无异常
        
        Returns:
            分数 [0, 0.1]
        """
        score = 0.0
        node_type = node.get("type")
        
        if node_type == "EXTRACT":
            extracted = page_state.get("extracted_data", {})
            expected_fields = node.get("params", {}).get("fields", [])
            if expected_fields:
                completeness = len([f for f in expected_fields if f in extracted]) / len(expected_fields)
                score = completeness * 0.1
            elif extracted:
                score = 0.1
                
        elif node_type == "COLLECT":
            collected = page_state.get("collected_items", [])
            if len(collected) > 0:
                score = 0.1
                
        elif node_type == "COMPUTE":
            if not page_state.get("compute_error"):
                score = 0.1
                
        elif node_type == "NAVIGATE":
            if page_state.get("navigation_success"):
                score = 0.1
                
        return score
    
    def _check_url_pattern(self, predicate: str, current_url: str) -> bool:
        """检查URL模式"""
        if not predicate or not current_url:
            return False
            
        # 提取URL相关的断言
        url_patterns = re.findall(r'URL[包含|匹配|等于][\s]*["\']?([^"\']+)["\']?', predicate)
        
        for pattern in url_patterns:
            if pattern.lower() in current_url.lower():
                return True
                
        return False
    
    def _check_title_match(self, predicate: str, page_title: str) -> bool:
        """检查页面标题"""
        if not predicate or not page_title:
            return False
            
        # 提取标题相关的断言
        title_patterns = re.findall(r'标题[包含|匹配|等于][\s]*["\']?([^"\']+)["\']?', predicate)
        
        for pattern in title_patterns:
            if pattern.lower() in page_title.lower():
                return True
                
        return False
    
    def _check_dom_elements(self, node: Dict, dom_elements: list) -> bool:
        """检查DOM元素"""
        required_elements = node.get("params", {}).get("required_elements", [])
        
        if not required_elements:
            return True
            
        # 简化检查：至少找到一个必需元素
        return len(dom_elements) > 0
    
    def _simple_semantic_check(self, node: Dict, page_state: Dict) -> float:
        """简单语义检查（无LLM）"""
        goal = node.get("goal", "").lower()
        content = page_state.get("text_content", "").lower()
        
        # 关键词匹配
        keywords = goal.split()
        matches = sum(1 for kw in keywords if kw in content)
        
        if not keywords:
            return 0.0
            
        confidence = matches / len(keywords)
        return confidence * 0.3
    
    def _parse_soft_check_response(self, response: str) -> float:
        """解析软验证响应"""
        # 提取置信度
        match = re.search(r'(\d+)', response)
        if match:
            confidence = int(match.group(1)) / 100.0
            return min(confidence, 1.0)
        
        # 简单的是/否判断
        if "是" in response or "yes" in response.lower():
            return 0.8
        else:
            return 0.2

