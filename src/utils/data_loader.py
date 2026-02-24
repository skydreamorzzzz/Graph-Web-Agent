"""
数据集加载器 - 支持多种Web Agent Benchmark
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum


class BenchmarkType(Enum):
    """Benchmark类型"""
    MINIWOB = "miniwob"
    WEBARENA = "webarena"
    WEBCHORE = "webchore"
    CUSTOM = "custom"


class DatasetLoader:
    """数据集加载器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_tasks(
        self, 
        benchmark: str = "miniwob",
        split: str = "test",
        num_tasks: Optional[int] = None
    ) -> List[Dict]:
        """
        加载任务
        
        Args:
            benchmark: 数据集名称 (miniwob, webarena, webchore)
            split: 数据集划分 (train, dev, test)
            num_tasks: 加载任务数量限制
            
        Returns:
            任务列表
        """
        benchmark_type = BenchmarkType(benchmark.lower())
        
        if benchmark_type == BenchmarkType.MINIWOB:
            tasks = self._load_miniwob_tasks(split)
        elif benchmark_type == BenchmarkType.WEBARENA:
            tasks = self._load_webarena_tasks(split)
        elif benchmark_type == BenchmarkType.WEBCHORE:
            tasks = self._load_webchore_tasks(split)
        else:
            tasks = self._load_custom_tasks(split)
        
        # 限制任务数量
        if num_tasks is not None:
            tasks = tasks[:num_tasks]
        
        return tasks
    
    def _load_miniwob_tasks(self, split: str = "test") -> List[Dict]:
        """
        加载MiniWoB++任务
        
        MiniWoB++特点:
        - 小规模、快速测试
        - 100+个任务类型
        - 每个任务都是独立的HTML页面
        - 适合快速验证和调试
        """
        # 尝试从processed目录加载
        processed_file = self.data_dir / "processed" / f"miniwob_{split}.json"
        if processed_file.exists():
            with open(processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("tasks", [])
        
        # 尝试从raw目录加载
        raw_file = self.data_dir / "raw" / "miniwob" / "tasks.json"
        if raw_file.exists():
            with open(raw_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
                return self._convert_miniwob_format(tasks)
        
        # 如果都不存在，返回示例任务
        print(f"警告: 未找到MiniWoB++数据文件，使用示例任务")
        return self._get_miniwob_sample_tasks()
    
    def _load_webarena_tasks(self, split: str = "test") -> List[Dict]:
        """
        加载WebArena任务
        
        WebArena特点:
        - 大规模、真实网站
        - 复杂的多步骤任务
        - 需要更长的执行时间
        """
        processed_file = self.data_dir / "processed" / f"webarena_{split}.json"
        if processed_file.exists():
            with open(processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("tasks", [])
        
        raw_file = self.data_dir / "raw" / "webarena" / "tasks.json"
        if raw_file.exists():
            with open(raw_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
                return self._convert_webarena_format(tasks)
        
        print(f"警告: 未找到WebArena数据文件，使用示例任务")
        return self._get_webarena_sample_tasks()
    
    def _load_webchore_tasks(self, split: str = "test") -> List[Dict]:
        """加载WebChoreArena任务"""
        processed_file = self.data_dir / "processed" / f"webchore_{split}.json"
        if processed_file.exists():
            with open(processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("tasks", [])
        
        print(f"警告: 未找到WebChoreArena数据文件")
        return []
    
    def _load_custom_tasks(self, split: str = "test") -> List[Dict]:
        """加载自定义任务"""
        custom_file = self.data_dir / "processed" / f"custom_{split}.json"
        if custom_file.exists():
            with open(custom_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("tasks", [])
        return []
    
    def _convert_miniwob_format(self, raw_tasks: List[Dict]) -> List[Dict]:
        """转换MiniWoB++格式为标准格式"""
        converted = []
        for task in raw_tasks:
            converted.append({
                "task_id": task.get("id", task.get("task_id")),
                "instruction": task.get("utterance", task.get("instruction")),
                "start_url": task.get("url", "http://localhost:8000"),  # MiniWoB++本地服务
                "task_type": task.get("task", "unknown"),
                "success_criteria": {
                    "type": "miniwob_reward",
                    "threshold": 1.0
                },
                "category": self._get_miniwob_category(task.get("task", "")),
                "difficulty": "easy",  # MiniWoB++任务相对简单
                "max_steps": 20,  # MiniWoB++任务步数较少
                "timeout": 60,
                "benchmark": "miniwob",
                "metadata": task.get("metadata", {})
            })
        return converted
    
    def _convert_webarena_format(self, raw_tasks: List[Dict]) -> List[Dict]:
        """转换WebArena格式为标准格式"""
        converted = []
        for task in raw_tasks:
            converted.append({
                "task_id": task.get("task_id"),
                "instruction": task.get("intent", task.get("instruction")),
                "start_url": task.get("start_url", ""),
                "target_url": task.get("target_url", ""),
                "success_criteria": task.get("eval", task.get("success_criteria", {})),
                "category": task.get("sites", ["unknown"])[0] if isinstance(task.get("sites"), list) else "unknown",
                "difficulty": task.get("difficulty", "medium"),
                "max_steps": 100,  # WebArena任务步数较多
                "timeout": 300,
                "benchmark": "webarena",
                "metadata": task.get("metadata", {})
            })
        return converted
    
    def _get_miniwob_category(self, task_name: str) -> str:
        """根据任务名称推断MiniWoB++类别"""
        if "click" in task_name.lower():
            return "click"
        elif "text" in task_name.lower() or "type" in task_name.lower():
            return "text_input"
        elif "search" in task_name.lower():
            return "search"
        elif "form" in task_name.lower():
            return "form_filling"
        elif "navigate" in task_name.lower():
            return "navigation"
        else:
            return "other"
    
    def _get_miniwob_sample_tasks(self) -> List[Dict]:
        """获取MiniWoB++示例任务"""
        return [
            {
                "task_id": "miniwob_click_test_001",
                "instruction": "点击标记为'Submit'的按钮",
                "start_url": "http://localhost:8000/click-test.html",
                "task_type": "click-test",
                "success_criteria": {"type": "miniwob_reward", "threshold": 1.0},
                "category": "click",
                "difficulty": "easy",
                "max_steps": 10,
                "timeout": 30,
                "benchmark": "miniwob"
            },
            {
                "task_id": "miniwob_click_button_001",
                "instruction": "点击按钮",
                "start_url": "http://localhost:8000/click-button.html",
                "task_type": "click-button",
                "success_criteria": {"type": "miniwob_reward", "threshold": 1.0},
                "category": "click",
                "difficulty": "easy",
                "max_steps": 10,
                "timeout": 30,
                "benchmark": "miniwob"
            },
            {
                "task_id": "miniwob_enter_text_001",
                "instruction": "在文本框中输入'Hello World'",
                "start_url": "http://localhost:8000/enter-text.html",
                "task_type": "enter-text",
                "success_criteria": {"type": "miniwob_reward", "threshold": 1.0},
                "category": "text_input",
                "difficulty": "easy",
                "max_steps": 10,
                "timeout": 30,
                "benchmark": "miniwob"
            }
        ]
    
    def _get_webarena_sample_tasks(self) -> List[Dict]:
        """获取WebArena示例任务"""
        return [
            {
                "task_id": "webarena_001",
                "instruction": "在Wikipedia上搜索'Python programming'并提取第一段内容",
                "start_url": "https://www.wikipedia.org/",
                "target_url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "success_criteria": {
                    "type": "text_match",
                    "expected": "Python is a high-level programming language"
                },
                "category": "wikipedia",
                "difficulty": "medium",
                "max_steps": 50,
                "timeout": 180,
                "benchmark": "webarena"
            }
        ]
    
    def save_results(
        self, 
        results: List[Dict], 
        benchmark: str,
        experiment_id: str,
        variant: str = "full_system"
    ):
        """
        保存实验结果
        
        Args:
            results: 结果列表
            benchmark: 数据集名称
            experiment_id: 实验ID
            variant: 实验变体
        """
        output_dir = self.data_dir / "output" / "predictions" / benchmark
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "experiment_id": experiment_id,
            "benchmark": benchmark,
            "variant": variant,
            "total_tasks": len(results),
            "results": results,
            "summary": self._compute_summary(results)
        }
        
        file_path = output_dir / f"{experiment_id}_{variant}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"结果已保存: {file_path}")
    
    def _compute_summary(self, results: List[Dict]) -> Dict:
        """计算结果摘要"""
        if not results:
            return {}
        
        success_count = sum(1 for r in results if r.get("success", False))
        total_steps = sum(r.get("steps", 0) for r in results)
        total_cost = sum(r.get("cost", 0) for r in results)
        
        return {
            "success_rate": success_count / len(results) if results else 0,
            "avg_steps": total_steps / len(results) if results else 0,
            "avg_cost": total_cost / len(results) if results else 0,
            "total_cost": total_cost
        }
    
    def get_benchmark_info(self, benchmark: str) -> Dict:
        """获取Benchmark信息"""
        info = {
            "miniwob": {
                "name": "MiniWoB++",
                "description": "小规模Web任务，适合快速测试",
                "task_count": "100+",
                "avg_steps": "5-15",
                "avg_time": "10-30秒",
                "difficulty": "简单",
                "url": "https://miniwob.farama.org/"
            },
            "webarena": {
                "name": "WebArena",
                "description": "大规模真实网站任务",
                "task_count": "812",
                "avg_steps": "20-50",
                "avg_time": "1-5分钟",
                "difficulty": "中等到困难",
                "url": "https://webarena.dev/"
            },
            "webchore": {
                "name": "WebChoreArena",
                "description": "日常Web任务",
                "task_count": "300+",
                "avg_steps": "15-40",
                "avg_time": "30秒-3分钟",
                "difficulty": "中等",
                "url": "https://github.com/..."
            }
        }
        return info.get(benchmark.lower(), {})

