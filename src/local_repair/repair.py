"""
Local Repair Engine - 局部修复引擎
"""
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class FailureType(Enum):
    """失败类型"""
    GROUNDING_FAIL = "grounding_fail"  # 元素定位失败
    STATE_FAIL = "state_fail"  # 状态不符合预期
    EXTRACTION_FAIL = "extraction_fail"  # 提取失败
    COMPUTE_FAIL = "compute_fail"  # 计算失败
    PLAN_FAIL = "plan_fail"  # 计划失败
    UNKNOWN = "unknown"


@dataclass
class RepairStrategy:
    """修复策略"""
    failure_type: FailureType
    strategy_name: str
    actions: List[str]
    rollback_depth: int  # 回滚深度


class LocalRepairEngine:
    """局部修复引擎"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_repair_per_node = self.config.get("max_repair_per_node", 3)
        
        # 修复策略表
        self.repair_strategies = self._init_repair_strategies()
        
    def _init_repair_strategies(self) -> Dict[FailureType, List[RepairStrategy]]:
        """初始化修复策略表"""
        return {
            FailureType.GROUNDING_FAIL: [
                RepairStrategy(
                    failure_type=FailureType.GROUNDING_FAIL,
                    strategy_name="切换锚点",
                    actions=["try_alternative_selector", "use_text_match", "use_xpath"],
                    rollback_depth=0
                ),
                RepairStrategy(
                    failure_type=FailureType.GROUNDING_FAIL,
                    strategy_name="等待元素出现",
                    actions=["wait_longer", "scroll_to_view"],
                    rollback_depth=0
                )
            ],
            FailureType.STATE_FAIL: [
                RepairStrategy(
                    failure_type=FailureType.STATE_FAIL,
                    strategy_name="关闭弹窗",
                    actions=["close_popup", "dismiss_modal"],
                    rollback_depth=0
                ),
                RepairStrategy(
                    failure_type=FailureType.STATE_FAIL,
                    strategy_name="重新导航",
                    actions=["refresh_page", "navigate_again"],
                    rollback_depth=1
                )
            ],
            FailureType.EXTRACTION_FAIL: [
                RepairStrategy(
                    failure_type=FailureType.EXTRACTION_FAIL,
                    strategy_name="扩展页面集合",
                    actions=["try_next_page", "expand_section"],
                    rollback_depth=0
                ),
                RepairStrategy(
                    failure_type=FailureType.EXTRACTION_FAIL,
                    strategy_name="调整提取规则",
                    actions=["relax_extraction_rules", "use_alternative_fields"],
                    rollback_depth=0
                )
            ],
            FailureType.COMPUTE_FAIL: [
                RepairStrategy(
                    failure_type=FailureType.COMPUTE_FAIL,
                    strategy_name="代码反思",
                    actions=["fix_computation", "use_fallback_value"],
                    rollback_depth=0
                )
            ],
            FailureType.PLAN_FAIL: [
                RepairStrategy(
                    failure_type=FailureType.PLAN_FAIL,
                    strategy_name="回滚至COLLECT",
                    actions=["rollback_to_collect"],
                    rollback_depth=2
                )
            ]
        }
    
    def classify_failure(self, node: Dict, verification_result, page_state: Dict) -> FailureType:
        """
        分类失败类型
        
        Args:
            node: 失败的节点
            verification_result: 验证结果
            page_state: 页面状态
            
        Returns:
            失败类型
        """
        node_type = node.get("type")
        
        # 安全获取错误信息
        error = ""
        if verification_result and hasattr(verification_result, 'details'):
            error = verification_result.details.get("error", "")
        elif isinstance(verification_result, dict):
            error = verification_result.get("details", {}).get("error", "")
        
        # 基于节点类型和错误信息分类
        if "element" in error.lower() or "selector" in error.lower():
            return FailureType.GROUNDING_FAIL
            
        if node_type == "EXTRACT":
            extracted = page_state.get("extracted_data", {})
            if not extracted or len(extracted) == 0:
                return FailureType.EXTRACTION_FAIL
                
        if node_type == "COMPUTE":
            if page_state.get("compute_error"):
                return FailureType.COMPUTE_FAIL
                
        if node_type in ["NAVIGATE", "ACT"]:
            # 检查是否有弹窗或状态异常
            if self._detect_popup(page_state):
                return FailureType.STATE_FAIL
                
        # 验证分数过低
        confidence = 0.0
        if verification_result and hasattr(verification_result, 'confidence'):
            confidence = verification_result.confidence
        elif isinstance(verification_result, dict):
            confidence = verification_result.get("confidence", 0.0)
            
        if confidence < 0.3:
            return FailureType.PLAN_FAIL
            
        return FailureType.UNKNOWN
    
    def select_repair_strategy(self, failure_type: FailureType, attempt: int) -> Optional[RepairStrategy]:
        """
        选择修复策略
        
        Args:
            failure_type: 失败类型
            attempt: 尝试次数（从0开始）
            
        Returns:
            修复策略，如果没有可用策略则返回None
        """
        strategies = self.repair_strategies.get(failure_type, [])
        
        if attempt >= len(strategies):
            return None
            
        return strategies[attempt]
    
    def compute_rollback_subgraph(
        self, 
        task_graph: Dict, 
        failed_node_id: str,
        failure_type: FailureType
    ) -> Tuple[List[str], int]:
        """
        计算最小回滚子图
        
        Args:
            task_graph: 任务图
            failed_node_id: 失败节点ID
            failure_type: 失败类型
            
        Returns:
            (需要重新执行的节点列表, 回滚深度)
        """
        # 获取修复策略的回滚深度
        strategy = self.select_repair_strategy(failure_type, 0)
        if not strategy:
            return [failed_node_id], 0
            
        rollback_depth = strategy.rollback_depth
        
        # 找到失败节点的祖先
        ancestors = self._find_ancestors(task_graph, failed_node_id, rollback_depth)
        
        # 构建需要重新执行的子图
        subgraph_nodes = ancestors + [failed_node_id]
        
        # 添加失败节点的所有后继节点
        descendants = self._find_descendants(task_graph, failed_node_id)
        subgraph_nodes.extend(descendants)
        
        # 去重并保持拓扑顺序
        from task_compiler.validator import GraphValidator
        validator = GraphValidator()
        topo_order = validator.get_topological_order(
            task_graph["nodes"],
            task_graph["edges"]
        )
        
        ordered_subgraph = [nid for nid in topo_order if nid in subgraph_nodes]
        
        return ordered_subgraph, rollback_depth
    
    def apply_repair(
        self,
        strategy: RepairStrategy,
        node: Dict,
        browser_env,
        page_state: Dict,
        check_idempotent: bool = True
    ) -> bool:
        """
        应用修复策略
        
        Args:
            strategy: 修复策略
            node: 节点
            browser_env: 浏览器环境
            page_state: 页面状态
            check_idempotent: 是否检查幂等性
            
        Returns:
            是否修复成功
        """
        print(f"应用修复策略: {strategy.strategy_name}")
        
        # 检查幂等性
        is_idempotent = node.get("idempotent", True)
        if check_idempotent and not is_idempotent:
            print(f"  警告: 节点{node.get('id')}非幂等，修复可能需要环境重置")
            # 非幂等节点修复前应该回滚或重置环境
            # 这里简化处理，实际应该由调用者处理
        
        for action in strategy.actions:
            try:
                success = self._execute_repair_action(action, node, browser_env, page_state)
                if success:
                    return True
            except Exception as e:
                print(f"  修复动作失败 {action}: {e}")
                continue
                
        return False
    
    def _execute_repair_action(
        self,
        action: str,
        node: Dict,
        browser_env,
        page_state: Dict
    ) -> bool:
        """执行修复动作"""
        if action == "close_popup":
            return self._close_popup(browser_env)
            
        elif action == "dismiss_modal":
            return self._dismiss_modal(browser_env)
            
        elif action == "refresh_page":
            browser_env.refresh()
            return True
            
        elif action == "wait_longer":
            browser_env.wait(5000)
            return True
            
        elif action == "scroll_to_view":
            browser_env.scroll_to_bottom()
            return True
            
        elif action == "try_alternative_selector":
            # 尝试备用选择器
            return self._try_alternative_selector(node, browser_env)
            
        elif action == "try_next_page":
            # 尝试翻页
            return self._try_pagination(browser_env)
            
        return False
    
    def _find_ancestors(self, task_graph: Dict, node_id: str, depth: int) -> List[str]:
        """找到节点的祖先（向上depth层）"""
        if depth == 0:
            return []
            
        edges = task_graph.get("edges", [])
        
        # 构建反向图
        reverse_graph = {}
        for from_node, to_node in edges:
            if to_node not in reverse_graph:
                reverse_graph[to_node] = []
            reverse_graph[to_node].append(from_node)
        
        # BFS向上查找
        ancestors = []
        current_level = [node_id]
        
        for _ in range(depth):
            next_level = []
            for node in current_level:
                parents = reverse_graph.get(node, [])
                next_level.extend(parents)
                ancestors.extend(parents)
            current_level = next_level
            
        return list(set(ancestors))
    
    def _find_descendants(self, task_graph: Dict, node_id: str) -> List[str]:
        """找到节点的所有后继节点"""
        edges = task_graph.get("edges", [])
        
        # 构建邻接表
        graph = {}
        for from_node, to_node in edges:
            if from_node not in graph:
                graph[from_node] = []
            graph[from_node].append(to_node)
        
        # DFS查找所有后继
        descendants = []
        visited = set()
        
        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            
            for child in graph.get(node, []):
                descendants.append(child)
                dfs(child)
        
        dfs(node_id)
        return descendants
    
    def _detect_popup(self, page_state: Dict) -> bool:
        """检测是否有弹窗"""
        # 简化实现：检查DOM中是否有modal相关元素
        dom_elements = page_state.get("dom_elements", [])
        modal_keywords = ["modal", "popup", "dialog", "overlay"]
        
        for element in dom_elements:
            element_str = str(element).lower()
            if any(kw in element_str for kw in modal_keywords):
                return True
                
        return False
    
    def _close_popup(self, browser_env) -> bool:
        """关闭弹窗"""
        try:
            # 尝试常见的关闭按钮选择器
            close_selectors = [
                "button.close",
                ".modal-close",
                "[aria-label='Close']",
                ".popup-close"
            ]
            
            for selector in close_selectors:
                if browser_env.click(selector, timeout=1000):
                    return True
                    
            # 尝试按ESC键
            browser_env.press_key("Escape")
            return True
            
        except Exception:
            return False
    
    def _dismiss_modal(self, browser_env) -> bool:
        """关闭模态框"""
        return self._close_popup(browser_env)
    
    def _try_alternative_selector(self, node: Dict, browser_env) -> bool:
        """尝试备用选择器"""
        # 简化实现
        return False
    
    def _try_pagination(self, browser_env) -> bool:
        """尝试翻页"""
        try:
            next_selectors = [
                "a.next",
                "button.next",
                "[aria-label='Next']",
                ".pagination-next"
            ]
            
            for selector in next_selectors:
                if browser_env.click(selector, timeout=1000):
                    return True
                    
        except Exception:
            pass
            
        return False

