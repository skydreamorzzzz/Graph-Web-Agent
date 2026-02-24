"""
Logger - 日志工具
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class TaskLogger:
    """任务日志记录器"""
    
    def __init__(self, log_dir: str = "results/logs", level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        self.logger = logging.getLogger("GraphWebAgent")
        self.logger.setLevel(getattr(logging, level))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
    def log_task_start(self, task_id: str, task_description: str) -> None:
        """记录任务开始"""
        self.logger.info(f"任务开始: {task_id}")
        self.logger.info(f"描述: {task_description}")
        
    def log_task_end(self, task_id: str, result: Dict[str, Any]) -> None:
        """记录任务结束"""
        success = result.get("success", False)
        status = "成功" if success else "失败"
        self.logger.info(f"任务结束: {task_id} - {status}")
        
        # 保存详细结果到文件
        self._save_task_result(task_id, result)
        
    def log_node_execution(self, node_id: str, node_type: str, status: str) -> None:
        """记录节点执行"""
        self.logger.info(f"节点 {node_id} ({node_type}): {status}")
        
    def log_repair_attempt(self, node_id: str, failure_type: str, strategy: str) -> None:
        """记录修复尝试"""
        self.logger.warning(f"修复尝试 - 节点: {node_id}, 失败类型: {failure_type}, 策略: {strategy}")
        
    def log_verification(self, node_id: str, confidence: float, passed: bool) -> None:
        """记录验证结果"""
        status = "通过" if passed else "未通过"
        self.logger.info(f"验证 - 节点: {node_id}, 置信度: {confidence:.2f}, 状态: {status}")
        
    def log_cost(self, stats: Dict[str, Any]) -> None:
        """记录成本统计"""
        self.logger.info(f"成本统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
    def _save_task_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """保存任务结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.log_dir / f"{task_id}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"结果已保存: {filename}")


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = {
            "success_count": 0,
            "failure_count": 0,
            "total_steps": 0,
            "total_llm_calls": 0,
            "total_cost": 0.0,
            "total_duration": 0.0,
            "failure_types": {},
            "repair_depths": [],
            "tasks": []
        }
        
    def record_task(self, result: Dict[str, Any]) -> None:
        """记录任务结果"""
        if result.get("success"):
            self.metrics["success_count"] += 1
        else:
            self.metrics["failure_count"] += 1
            
        self.metrics["total_steps"] += result.get("steps", 0)
        self.metrics["total_duration"] += result.get("duration", 0.0)
        
        # 记录任务详情
        self.metrics["tasks"].append({
            "task_id": result.get("task_id"),
            "success": result.get("success"),
            "steps": result.get("steps"),
            "duration": result.get("duration")
        })
        
    def record_cost(self, cost_stats: Dict[str, Any]) -> None:
        """记录成本"""
        self.metrics["total_llm_calls"] += cost_stats.get("total_calls", 0)
        self.metrics["total_cost"] += cost_stats.get("total_cost", 0.0)
        
    def record_failure(self, failure_type: str) -> None:
        """记录失败类型"""
        if failure_type not in self.metrics["failure_types"]:
            self.metrics["failure_types"][failure_type] = 0
        self.metrics["failure_types"][failure_type] += 1
        
    def record_repair_depth(self, depth: int) -> None:
        """记录修复深度"""
        self.metrics["repair_depths"].append(depth)
        
    def get_summary(self) -> Dict[str, Any]:
        """获取汇总统计"""
        total_tasks = self.metrics["success_count"] + self.metrics["failure_count"]
        
        summary = {
            "total_tasks": total_tasks,
            "success_rate": (
                self.metrics["success_count"] / total_tasks 
                if total_tasks > 0 else 0
            ),
            "avg_steps": (
                self.metrics["total_steps"] / total_tasks 
                if total_tasks > 0 else 0
            ),
            "avg_llm_calls": (
                self.metrics["total_llm_calls"] / total_tasks 
                if total_tasks > 0 else 0
            ),
            "cost_per_success": (
                self.metrics["total_cost"] / self.metrics["success_count"]
                if self.metrics["success_count"] > 0 else 0
            ),
            "avg_duration": (
                self.metrics["total_duration"] / total_tasks
                if total_tasks > 0 else 0
            ),
            "failure_distribution": self.metrics["failure_types"],
            "avg_repair_depth": (
                sum(self.metrics["repair_depths"]) / len(self.metrics["repair_depths"])
                if self.metrics["repair_depths"] else 0
            )
        }
        
        return summary
    
    def save_metrics(self, filepath: str) -> None:
        """保存指标到文件"""
        summary = self.get_summary()
        summary["raw_metrics"] = self.metrics
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


