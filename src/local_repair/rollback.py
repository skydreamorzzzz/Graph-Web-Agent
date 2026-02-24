"""
Rollback Manager - 回滚管理器
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import copy


@dataclass
class Checkpoint:
    """检查点"""
    node_id: str
    step: int
    page_state: Dict
    browser_state: Dict
    timestamp: float


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, max_checkpoints: int = 10):
        self.max_checkpoints = max_checkpoints
        self.checkpoints: List[Checkpoint] = []
        self.rollback_history: List[Dict] = []
        
    def save_checkpoint(
        self,
        node_id: str,
        step: int,
        page_state: Dict,
        browser_state: Dict
    ) -> None:
        """
        保存检查点
        
        Args:
            node_id: 节点ID
            step: 步骤数
            page_state: 页面状态
            browser_state: 浏览器状态
        """
        import time
        
        checkpoint = Checkpoint(
            node_id=node_id,
            step=step,
            page_state=copy.deepcopy(page_state),
            browser_state=copy.deepcopy(browser_state),
            timestamp=time.time()
        )
        
        self.checkpoints.append(checkpoint)
        
        # 限制检查点数量
        if len(self.checkpoints) > self.max_checkpoints:
            self.checkpoints.pop(0)
    
    def rollback_to_node(self, node_id: str) -> Optional[Checkpoint]:
        """
        回滚到指定节点
        
        Args:
            node_id: 目标节点ID
            
        Returns:
            检查点，如果找不到则返回None
        """
        # 从后向前查找
        for i in range(len(self.checkpoints) - 1, -1, -1):
            checkpoint = self.checkpoints[i]
            if checkpoint.node_id == node_id:
                # 记录回滚历史
                self.rollback_history.append({
                    "from_step": self.checkpoints[-1].step if self.checkpoints else 0,
                    "to_step": checkpoint.step,
                    "to_node": node_id
                })
                
                # 删除该检查点之后的所有检查点
                self.checkpoints = self.checkpoints[:i+1]
                
                return checkpoint
                
        return None
    
    def rollback_steps(self, steps: int) -> Optional[Checkpoint]:
        """
        回滚指定步数
        
        Args:
            steps: 回滚步数
            
        Returns:
            检查点
        """
        if not self.checkpoints or steps <= 0:
            return None
            
        target_index = max(0, len(self.checkpoints) - steps - 1)
        checkpoint = self.checkpoints[target_index]
        
        # 记录回滚历史
        self.rollback_history.append({
            "from_step": self.checkpoints[-1].step,
            "to_step": checkpoint.step,
            "steps_back": steps
        })
        
        # 删除目标检查点之后的所有检查点
        self.checkpoints = self.checkpoints[:target_index+1]
        
        return checkpoint
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """获取最新检查点"""
        return self.checkpoints[-1] if self.checkpoints else None
    
    def clear_checkpoints(self) -> None:
        """清除所有检查点"""
        self.checkpoints.clear()
        
    def get_rollback_stats(self) -> Dict[str, Any]:
        """获取回滚统计信息"""
        return {
            "total_rollbacks": len(self.rollback_history),
            "checkpoint_count": len(self.checkpoints),
            "rollback_history": self.rollback_history
        }


class EnvironmentReset:
    """环境重置"""
    
    def __init__(self, browser_env):
        self.browser = browser_env
        self.initial_state = None
        
    def save_initial_state(self) -> None:
        """保存初始状态"""
        self.initial_state = {
            "url": self.browser.get_url(),
            "cookies": self.browser.get_cookies(),
            "local_storage": self.browser.get_local_storage()
        }
    
    def reset_to_initial(self) -> None:
        """重置到初始状态"""
        if not self.initial_state:
            return
            
        # 清除cookies和storage
        self.browser.clear_cookies()
        self.browser.clear_local_storage()
        
        # 恢复初始cookies
        for cookie in self.initial_state.get("cookies", []):
            self.browser.set_cookie(cookie)
            
        # 导航到初始URL
        initial_url = self.initial_state.get("url")
        if initial_url:
            self.browser.navigate(initial_url)
    
    def reset_page(self) -> None:
        """重置当前页面"""
        self.browser.refresh()
        
    def close_all_popups(self) -> None:
        """关闭所有弹窗"""
        # 尝试多次按ESC
        for _ in range(3):
            self.browser.press_key("Escape")
            self.browser.wait(500)


class NoProgressDetector:
    """无进展检测器"""
    
    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self.dom_hashes: List[str] = []
        
    def record_dom_state(self, page_state: Dict) -> None:
        """记录DOM状态"""
        import hashlib
        
        # 计算DOM的哈希值
        dom_content = str(page_state.get("dom_elements", []))
        dom_hash = hashlib.md5(dom_content.encode()).hexdigest()
        
        self.dom_hashes.append(dom_hash)
        
        # 限制窗口大小
        if len(self.dom_hashes) > self.window_size:
            self.dom_hashes.pop(0)
    
    def detect_no_progress(self) -> bool:
        """
        检测是否无进展
        
        Returns:
            如果DOM连续不变则返回True
        """
        if len(self.dom_hashes) < self.window_size:
            return False
            
        # 检查最近的DOM哈希是否都相同
        return len(set(self.dom_hashes)) == 1
    
    def reset(self) -> None:
        """重置检测器"""
        self.dom_hashes.clear()


