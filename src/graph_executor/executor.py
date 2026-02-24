"""
Graph Executor - 任务图执行器
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionContext:
    """执行上下文"""
    task_graph: Dict
    current_node: Optional[str] = None
    node_states: Dict[str, NodeStatus] = field(default_factory=dict)
    node_results: Dict[str, Any] = field(default_factory=dict)
    page_state: Dict[str, Any] = field(default_factory=dict)
    step_count: int = 0
    start_time: float = 0.0
    repair_count: Dict[str, int] = field(default_factory=dict)


class GraphExecutor:
    """任务图执行器"""
    
    def __init__(self, browser_env, verifier, router=None, rollback_manager=None, config: Dict = None):
        """
        Args:
            browser_env: 浏览器环境
            verifier: 双路验证器
            router: 成本路由器
            rollback_manager: 回滚管理器
            config: 配置
        """
        self.browser = browser_env
        self.verifier = verifier
        self.router = router
        self.rollback_manager = rollback_manager
        self.config = config or {}
        self.max_steps = config.get("max_steps", 100)
        
        # 无进展检测器
        from local_repair.rollback import NoProgressDetector
        self.no_progress_detector = NoProgressDetector(window_size=3)
        
    def execute(self, task_graph: Dict) -> Dict[str, Any]:
        """
        执行任务图
        
        Args:
            task_graph: 任务图
            
        Returns:
            执行结果
        """
        # 初始化执行上下文
        context = ExecutionContext(
            task_graph=task_graph,
            start_time=time.time()
        )
        
        # 获取拓扑排序
        from task_compiler.validator import GraphValidator
        validator = GraphValidator()
        
        try:
            topo_order = validator.get_topological_order(
                task_graph["nodes"],
                task_graph["edges"]
            )
        except Exception as e:
            return self._create_error_result(f"拓扑排序失败: {e}", context)
        
        # 初始化节点状态
        for node_id in topo_order:
            context.node_states[node_id] = NodeStatus.PENDING
            context.repair_count[node_id] = 0
        
        # 按拓扑顺序执行节点
        for node_id in topo_order:
            if context.step_count >= self.max_steps:
                return self._create_error_result("超过最大步数限制", context)
            
            node = self._get_node_by_id(task_graph, node_id)
            if not node:
                continue
                
            # 执行节点
            success = self._execute_node(node, context)
            
            if not success:
                # 执行失败，返回结果
                return self._create_failure_result(node, context)
            
            context.step_count += 1
        
        # 所有节点执行成功
        return self._create_success_result(context)
    
    def _execute_node(self, node: Dict, context: ExecutionContext) -> bool:
        """
        执行单个节点
        
        Returns:
            是否成功
        """
        node_id = node["id"]
        node_type = node["type"]
        
        context.current_node = node_id
        context.node_states[node_id] = NodeStatus.RUNNING
        
        print(f"执行节点 {node_id} ({node_type}): {node.get('goal', '')}")
        
        try:
            # 1. 执行动作
            self._perform_action(node, context)
            
            # 2. 等待页面稳定
            self._wait_for_stability(context)
            
            # 3. 收集证据
            self._collect_evidence(node, context)
            
            # 4. 双路验证（使用成本路由）
            model_tier = None
            if self.router:
                model_tier = self.router.route(node, context.page_state, context.__dict__)
                print(f"  路由决策: {model_tier.value}")
            
            verification = self.verifier.verify(node, context.page_state, model_tier)
            
            # 记录LLM调用
            if self.router and model_tier:
                self.router.record_call(model_tier, node_id, input_tokens=100, output_tokens=50)
            
            print(f"  置信度: {verification.confidence:.2f} (通过: {verification.passed})")
            
            # 检测无进展
            self.no_progress_detector.record_dom_state(context.page_state)
            if self.no_progress_detector.detect_no_progress():
                print("  检测到无进展（DOM连续不变）")
                context.node_states[node_id] = NodeStatus.FAILED
                context.node_results[node_id] = {
                    "status": "failed",
                    "confidence": verification.confidence,
                    "verification": verification.to_dict(),  # 转换为字典
                    "reason": "无进展检测触发"
                }
                return False
            
            if verification.passed:
                context.node_states[node_id] = NodeStatus.SUCCESS
                context.node_results[node_id] = {
                    "status": "success",
                    "confidence": verification.confidence,
                    "verification": verification.to_dict()  # 转换为字典
                }
                
                # 保存检查点
                if self.rollback_manager:
                    browser_state = {
                        "url": self.browser.get_url(),
                        "cookies": self.browser.get_cookies(),
                        "local_storage": self.browser.get_local_storage()
                    }
                    self.rollback_manager.save_checkpoint(
                        node_id=node_id,
                        step=context.step_count,
                        page_state=context.page_state.copy(),
                        browser_state=browser_state
                    )
                
                # 记录成功
                if self.router:
                    self.router.record_success(node_id)
                
                return True
            else:
                context.node_states[node_id] = NodeStatus.FAILED
                context.node_results[node_id] = {
                    "status": "failed",
                    "confidence": verification.confidence,
                    "verification": verification.to_dict(),  # 转换为字典
                    "reason": "验证未通过"
                }
                
                # 记录失败
                if self.router:
                    self.router.record_failure(node_id)
                
                return False
                
        except Exception as e:
            print(f"  执行失败: {e}")
            context.node_states[node_id] = NodeStatus.FAILED
            context.node_results[node_id] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def _perform_action(self, node: Dict, context: ExecutionContext) -> None:
        """执行节点动作"""
        node_type = node["type"]
        params = node.get("params", {})
        
        if node_type == "NAVIGATE":
            url = params.get("url", "")
            if url:
                self.browser.navigate(url)
                context.page_state["navigation_success"] = True
                
        elif node_type == "COLLECT":
            selector = params.get("selector", "")
            items = self.browser.collect_elements(selector)
            context.page_state["collected_items"] = items
            context.page_state["dom_elements"] = items
            
        elif node_type == "EXTRACT":
            fields = params.get("fields", [])
            data = self.browser.extract_data(fields)
            context.page_state["extracted_data"] = data
            
        elif node_type == "COMPUTE":
            # 执行计算逻辑
            compute_fn = params.get("function")
            if compute_fn:
                try:
                    result = eval(compute_fn)  # 注意：实际应用中需要安全的执行方式
                    context.page_state["compute_result"] = result
                except Exception as e:
                    context.page_state["compute_error"] = str(e)
                    
        elif node_type == "ACT":
            action = params.get("action", "")
            target = params.get("target", "")
            
            if action == "click":
                self.browser.click(target)
            elif action == "type":
                text = params.get("text", "")
                self.browser.type_text(target, text)
            elif action == "submit":
                self.browser.submit(target)
                
            context.page_state["state_changed"] = True
            
        elif node_type == "VERIFY":
            # 验证节点主要依赖双路验证
            pass
            
        elif node_type == "ITERATE":
            # 迭代逻辑 - 运行时展开
            max_iterations = params.get("max_iterations", 10)
            collection = context.page_state.get("collected_items", [])
            
            print(f"  迭代处理 {len(collection)} 个项目（最多{max_iterations}次）")
            
            iteration_results = []
            for i, item in enumerate(collection[:max_iterations]):
                context.page_state["current_item"] = item
                context.page_state["iteration_index"] = i
                iteration_results.append(item)
            
            context.page_state["iteration_results"] = iteration_results
            context.page_state["state_changed"] = True
            
        elif node_type == "BRANCH":
            # 分支逻辑 - 运行时展开
            condition = params.get("condition", "")
            
            # 简单的条件评估
            try:
                # 从page_state中获取变量进行条件判断
                condition_result = self._evaluate_condition(condition, context.page_state)
                context.page_state["branch_taken"] = condition_result
                context.page_state["state_changed"] = True
                print(f"  分支条件 '{condition}' 结果: {condition_result}")
            except Exception as e:
                print(f"  分支条件评估失败: {e}")
                context.page_state["branch_taken"] = False
    
    def _wait_for_stability(self, context: ExecutionContext) -> None:
        """
        等待页面稳定 - WAIT_UNTIL机制
        连续N次DOM摘要一致才认为页面稳定
        """
        import hashlib
        import time
        
        max_attempts = 5
        stable_count = 0
        required_stable_count = 3
        timeout = self.config.get("wait_timeout", 10000)
        start_time = time.time() * 1000
        
        last_dom_hash = None
        
        while stable_count < required_stable_count:
            # 检查超时
            if (time.time() * 1000 - start_time) > timeout:
                print("  等待页面稳定超时")
                break
            
            # 等待一小段时间
            self.browser.wait(500)
            
            # 获取当前DOM摘要
            try:
                text_content = self.browser.get_text_content()
                dom_hash = hashlib.md5(text_content.encode()).hexdigest()
                
                if dom_hash == last_dom_hash:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_dom_hash = dom_hash
                    
            except Exception as e:
                print(f"  获取DOM摘要失败: {e}")
                break
        
        if stable_count >= required_stable_count:
            print(f"  页面已稳定（连续{stable_count}次DOM一致）")
    
    def _collect_evidence(self, node: Dict, context: ExecutionContext) -> None:
        """收集证据"""
        # 更新页面状态
        context.page_state.update({
            "url": self.browser.get_url(),
            "title": self.browser.get_title(),
            "text_content": self.browser.get_text_content(),
            "dom_elements": context.page_state.get("dom_elements", [])
        })
    
    def _get_node_by_id(self, task_graph: Dict, node_id: str) -> Optional[Dict]:
        """根据ID获取节点"""
        for node in task_graph.get("nodes", []):
            if node["id"] == node_id:
                return node
        return None
    
    def _create_success_result(self, context: ExecutionContext) -> Dict:
        """创建成功结果"""
        return {
            "success": True,
            "task_id": context.task_graph.get("task_id"),
            "steps": context.step_count,
            "duration": time.time() - context.start_time,
            "node_results": context.node_results,
            "final_state": context.page_state
        }
    
    def _create_failure_result(self, failed_node: Dict, context: ExecutionContext) -> Dict:
        """创建失败结果"""
        return {
            "success": False,
            "task_id": context.task_graph.get("task_id"),
            "failed_node": failed_node["id"],
            "steps": context.step_count,
            "duration": time.time() - context.start_time,
            "node_results": context.node_results,
            "error": context.node_results.get(failed_node["id"], {}).get("reason", "未知错误")
        }
    
    def _create_error_result(self, error_msg: str, context: ExecutionContext) -> Dict:
        """创建错误结果"""
        return {
            "success": False,
            "task_id": context.task_graph.get("task_id", "unknown"),
            "error": error_msg,
            "steps": context.step_count,
            "duration": time.time() - context.start_time
        }
    
    def _evaluate_condition(self, condition: str, page_state: Dict) -> bool:
        """
        评估分支条件
        
        Args:
            condition: 条件表达式
            page_state: 页面状态
            
        Returns:
            条件是否为真
        """
        # 简化实现：支持基本的条件判断
        # 实际应用中应该使用更安全的表达式评估
        try:
            # 创建安全的局部变量环境
            safe_locals = {
                "page_state": page_state,
                "url": page_state.get("url", ""),
                "title": page_state.get("title", ""),
                "extracted_data": page_state.get("extracted_data", {}),
                "collected_items": page_state.get("collected_items", [])
            }
            
            # 评估条件
            result = eval(condition, {"__builtins__": {}}, safe_locals)
            return bool(result)
        except Exception as e:
            print(f"条件评估错误: {e}")
            return False


