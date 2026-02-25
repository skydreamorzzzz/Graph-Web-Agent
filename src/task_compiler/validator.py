"""
Graph Validator - 验证任务图的合法性
"""
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, deque


class ValidationError(Exception):
    """验证错误"""
    pass


class GraphValidator:
    """任务图验证器"""
    
    VALID_NODE_TYPES = {
        "NAVIGATE", "COLLECT", "EXTRACT", 
        "COMPUTE", "ACT", "VERIFY", 
        "ITERATE", "BRANCH"
    }
    
    REQUIRED_NODE_FIELDS = {"id", "type", "goal", "predicate"}
    
    def __init__(self, auto_fix: bool = True):
        """
        Args:
            auto_fix: 是否自动修复可修复的错误
        """
        self.auto_fix = auto_fix
        self.errors = []
        self.warnings = []
        
    def validate(self, task_graph: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证任务图
        
        Args:
            task_graph: 任务图字典
            
        Returns:
            (是否有效, 错误列表)
        """
        self.errors = []
        self.warnings = []
        
        # 基本结构检查
        if not self._check_basic_structure(task_graph):
            return False, self.errors
            
        nodes = task_graph.get("nodes", [])
        edges = task_graph.get("edges", [])
        
        # 节点验证
        if not self._validate_nodes(nodes):
            return False, self.errors
            
        # 边验证
        if not self._validate_edges(edges, nodes):
            return False, self.errors
            
        # 拓扑验证
        if not self._validate_topology(nodes, edges):
            if self.auto_fix:
                # 记录当前错误后尝试修复，并重新验证
                self._fix_topology(task_graph)
                nodes = task_graph.get("nodes", [])
                edges = task_graph.get("edges", [])

                # 清理上一轮“图中存在环”的错误，避免重复
                self.errors = [e for e in self.errors if e != "图中存在环"]
                if not self._validate_topology(nodes, edges):
                    self.errors.append("自动修复后拓扑仍无效")
                    return False, self.errors
            else:
                return False, self.errors
                
        # 可达性验证
        if not self._validate_reachability(nodes, edges):
            return False, self.errors
            
        return True, self.errors
    
    def _check_basic_structure(self, task_graph: Dict) -> bool:
        """检查基本结构"""
        if not isinstance(task_graph, dict):
            self.errors.append("任务图必须是字典类型")
            return False
            
        if "nodes" not in task_graph:
            self.errors.append("缺少nodes字段")
            return False
            
        if "edges" not in task_graph:
            self.errors.append("缺少edges字段")
            return False
            
        return True
    
    def _validate_nodes(self, nodes: List[Dict]) -> bool:
        """验证节点"""
        if not nodes:
            self.errors.append("至少需要一个节点")
            return False
            
        node_ids = set()
        
        for i, node in enumerate(nodes):
            # 检查必需字段
            missing_fields = self.REQUIRED_NODE_FIELDS - set(node.keys())
            if missing_fields:
                self.errors.append(f"节点{i}缺少字段: {missing_fields}")
                return False
                
            # 检查节点ID唯一性
            node_id = node.get("id")
            if node_id in node_ids:
                self.errors.append(f"节点ID重复: {node_id}")
                return False
            node_ids.add(node_id)
            
            # 检查节点类型
            node_type = node.get("type")
            if node_type not in self.VALID_NODE_TYPES:
                self.errors.append(f"无效的节点类型: {node_type}")
                return False
                
        return True
    
    def _validate_edges(self, edges: List[List[str]], nodes: List[Dict]) -> bool:
        """验证边"""
        node_ids = {node["id"] for node in nodes}
        
        for edge in edges:
            if len(edge) != 2:
                self.errors.append(f"边格式错误: {edge}")
                return False
                
            from_node, to_node = edge
            
            if from_node not in node_ids:
                self.errors.append(f"边引用了不存在的节点: {from_node}")
                return False
                
            if to_node not in node_ids:
                self.errors.append(f"边引用了不存在的节点: {to_node}")
                return False
                
        return True
    
    def _validate_topology(self, nodes: List[Dict], edges: List[List[str]]) -> bool:
        """验证拓扑结构（无环）"""
        # 构建邻接表
        graph = defaultdict(list)
        for from_node, to_node in edges:
            graph[from_node].append(to_node)
            
        # DFS检测环
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
                    
            rec_stack.remove(node)
            return False
        
        for node in [n["id"] for n in nodes]:
            if node not in visited:
                if has_cycle(node):
                    self.errors.append("图中存在环")
                    return False
                    
        return True
    
    def _validate_reachability(self, nodes: List[Dict], edges: List[List[str]]) -> bool:
        """验证所有节点可达"""
        if not nodes:
            return True
            
        # 构建邻接表
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for from_node, to_node in edges:
            graph[from_node].append(to_node)
            in_degree[to_node] += 1
            
        # 找到起始节点（入度为0）
        start_nodes = [n["id"] for n in nodes if in_degree[n["id"]] == 0]
        
        if not start_nodes:
            self.warnings.append("没有找到起始节点（入度为0）")
            # 使用第一个节点作为起始节点
            start_nodes = [nodes[0]["id"]]
            
        # BFS检查可达性
        reachable = set()
        queue = deque(start_nodes)
        
        while queue:
            node = queue.popleft()
            if node in reachable:
                continue
            reachable.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in reachable:
                    queue.append(neighbor)
                    
        # 检查是否所有节点都可达
        all_nodes = {n["id"] for n in nodes}
        unreachable = all_nodes - reachable
        
        if unreachable:
            self.errors.append(f"以下节点不可达: {unreachable}")
            return False
            
        return True
    
    def _fix_topology(self, task_graph: Dict) -> None:
        """尝试修复拓扑问题"""
        # 简单修复：移除导致环的边
        # 这是一个简化实现，实际可能需要更复杂的逻辑
        self.warnings.append("尝试自动修复拓扑问题")
        
    def get_topological_order(self, nodes: List[Dict], edges: List[List[str]]) -> List[str]:
        """
        获取拓扑排序
        
        Returns:
            节点ID的拓扑排序列表
        """
        # 构建邻接表和入度表
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for node in nodes:
            in_degree[node["id"]] = 0
            
        for from_node, to_node in edges:
            graph[from_node].append(to_node)
            in_degree[to_node] += 1
            
        # Kahn算法
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if len(result) != len(nodes):
            raise ValidationError("无法生成拓扑排序，图中可能存在环")
            
        return result


