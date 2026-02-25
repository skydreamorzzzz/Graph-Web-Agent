"""
Main Experiment Runner - 主实验运行脚本
"""
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from task_compiler.compiler import TaskCompiler
from task_compiler.validator import GraphValidator
from graph_executor.executor import GraphExecutor
from graph_executor.dual_verifier import DualVerifier
from local_repair.repair import LocalRepairEngine
from local_repair.rollback import RollbackManager, EnvironmentReset, NoProgressDetector
from router.router import CostAwareRouter
from utils.logger import TaskLogger, MetricsCollector
from utils.data_loader import DatasetLoader
from models.model_loader import ModelLoader
from models.browser_env import PlaywrightBrowser


class ExperimentRunner:
    """实验运行器"""
    
    def __init__(self, config_path: str = "config/default_params.yaml"):
        # 确保使用项目根目录的路径
        if not Path(config_path).is_absolute():
            # 获取项目根目录（scripts的父目录）
            project_root = Path(__file__).parent.parent
            config_path = project_root / config_path
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化组件
        # 使用项目根目录的路径
        project_root = Path(__file__).parent.parent
        log_dir = self.config.get("logging", {}).get("log_dir", "results/logs")
        if not Path(log_dir).is_absolute():
            log_dir = project_root / log_dir
            
        self.logger = TaskLogger(
            log_dir=str(log_dir),
            level=self.config.get("logging", {}).get("level", "INFO")
        )
        
        self.metrics_collector = MetricsCollector()
        
        # 初始化模型加载器
        self.model_loader = ModelLoader(self.config.get("llm", {}))
        
        # 初始化浏览器环境
        env_config = self.config.get("environment", {})
        self.browser = PlaywrightBrowser(headless=env_config.get("headless", False))
        
        # 初始化各个模块
        self._init_modules()
        
    def _init_modules(self):
        """初始化各个模块"""
        # LLM客户端（用于任务编译和软验证）
        llm_config = self.config.get("llm", {})
        small_model = self.config.get("router", {}).get("small_model", "gpt-3.5-turbo")
        
        try:
            self.llm_client = self.model_loader.load_model(small_model)
        except Exception as e:
            self.logger.logger.warning(f"LLM加载失败，使用Mock模式: {e}")
            from models.model_loader import MockLLM
            self.llm_client = MockLLM(small_model)
        
        # 任务编译器
        self.compiler = TaskCompiler(llm_client=self.llm_client, config=self.config)
        
        # 图验证器
        self.validator = GraphValidator(auto_fix=True)
        
        # 双路验证器
        verification_config = self.config.get("verification", {})
        self.verifier = DualVerifier(config=verification_config, llm_client=self.llm_client)
        
        # 成本路由器
        router_config = self.config.get("router", {})
        self.router = CostAwareRouter(config=router_config)
        
        # 回滚管理器
        self.rollback_manager = RollbackManager(max_checkpoints=10)
        
        # 图执行器（集成路由器和回滚管理器）
        system_config = self.config.get("system", {})
        self.executor = GraphExecutor(
            browser_env=self.browser,
            verifier=self.verifier,
            router=self.router,
            rollback_manager=self.rollback_manager,
            config=system_config
        )
        
        # 局部修复引擎
        self.repair_engine = LocalRepairEngine(config=system_config)
        
        # 环境重置器
        from local_repair.rollback import EnvironmentReset
        self.env_reset = EnvironmentReset(self.browser)
        
        # 数据加载器
        self.data_loader = DatasetLoader()
        
    def run_task(self, task_description: str, task_id: str = None, use_repair: bool = True) -> dict:
        """
        运行单个任务
        
        Args:
            task_description: 任务描述
            task_id: 任务ID
            use_repair: 是否使用修复机制
            
        Returns:
            任务结果
        """
        if not task_id:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.log_task_start(task_id, task_description)
        
        try:
            # 1. 编译任务
            self.logger.logger.info("步骤1: 编译任务图...")
            task_graph = self.compiler.compile(task_description, task_id)
            
            # 保存任务图
            self._save_task_graph(task_graph)
            
            # 2. 验证任务图
            self.logger.logger.info("步骤2: 验证任务图...")
            is_valid, errors = self.validator.validate(task_graph)
            
            if not is_valid:
                self.logger.logger.error(f"任务图验证失败: {errors}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": f"任务图验证失败: {errors}"
                }
            
            # 3. 执行任务图
            self.logger.logger.info("步骤3: 执行任务图...")
            result = self.executor.execute(task_graph)
            
            # 4. 如果失败且启用修复，尝试修复
            if not result["success"] and use_repair:
                # 仅在存在明确失败节点时进行局部修复；执行级错误直接返回
                if result.get("failed_node"):
                    self.logger.logger.info("步骤4: 尝试局部修复...")
                    result = self._attempt_repair(task_graph, result)
                else:
                    self.logger.logger.warning(
                        f"跳过局部修复：未定位失败节点，错误={result.get('error', 'unknown')}"
                    )
            
            # 5. 记录结果
            self.logger.log_task_end(task_id, result)
            self.metrics_collector.record_task(result)
            
            # 6. 记录成本
            cost_stats = self.router.get_stats()
            self.metrics_collector.record_cost(cost_stats)
            self.logger.log_cost(cost_stats)
            
            return result
            
        except Exception as e:
            self.logger.logger.error(f"任务执行异常: {e}", exc_info=True)
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    def _attempt_repair(self, task_graph: dict, initial_result: dict) -> dict:
        """
        尝试修复失败的任务 - 完整的修复-回滚-重执行流程
        """
        failed_node_id = initial_result.get("failed_node")
        if not failed_node_id:
            return initial_result
        
        # 获取失败节点
        failed_node = None
        for node in task_graph["nodes"]:
            if node["id"] == failed_node_id:
                failed_node = node
                break
        
        if not failed_node:
            return initial_result
        
        # 分类失败
        verification_result = initial_result.get("node_results", {}).get(failed_node_id, {}).get("verification")
        page_state = initial_result.get("final_state", {})
        
        failure_type = self.repair_engine.classify_failure(
            failed_node,
            verification_result,
            page_state
        )
        
        self.logger.logger.info(f"失败类型: {failure_type.value}")
        self.metrics_collector.record_failure(failure_type.value)
        
        # 尝试修复（最多3次）
        max_attempts = self.config.get("system", {}).get("max_repair_per_node", 3)
        
        for attempt in range(max_attempts):
            strategy = self.repair_engine.select_repair_strategy(failure_type, attempt)
            
            if not strategy:
                self.logger.logger.warning("没有可用的修复策略")
                break
            
            self.logger.log_repair_attempt(failed_node_id, failure_type.value, strategy.strategy_name)
            
            # 步骤1: 计算最小回滚子图
            rollback_subgraph, rollback_depth = self.repair_engine.compute_rollback_subgraph(
                task_graph,
                failed_node_id,
                failure_type
            )
            
            self.logger.logger.info(f"回滚深度: {rollback_depth}, 子图节点: {rollback_subgraph}")
            
            # 步骤2: 回滚到检查点（如果需要）
            if rollback_depth > 0 and self.rollback_manager:
                # 找到回滚目标节点
                if len(rollback_subgraph) > 0:
                    target_node_id = rollback_subgraph[0]
                    checkpoint = self.rollback_manager.rollback_to_node(target_node_id)
                    
                    if checkpoint:
                        self.logger.logger.info(f"回滚到检查点: {target_node_id}")
                        # 恢复浏览器状态
                        self._restore_browser_state(checkpoint.browser_state)
                    else:
                        self.logger.logger.warning("未找到检查点，使用环境重置")
                        # 检查节点幂等性
                        is_idempotent = failed_node.get("idempotent", True)
                        if not is_idempotent:
                            self.env_reset.reset_to_initial()
            
            # 步骤3: 应用修复策略
            repair_success = self.repair_engine.apply_repair(
                strategy,
                failed_node,
                self.browser,
                page_state,
                check_idempotent=True
            )
            
            if not repair_success:
                self.logger.logger.warning(f"修复策略应用失败，尝试下一个策略")
                continue
            
            # 步骤4: 重新执行子图
            self.logger.logger.info(f"重新执行子图: {rollback_subgraph}")
            result = self._execute_subgraph(task_graph, rollback_subgraph)
            
            if result["success"]:
                self.logger.logger.info("修复成功！")
                self.metrics_collector.record_repair_depth(rollback_depth)
                return result
            else:
                self.logger.logger.warning(f"子图执行失败，尝试次数: {attempt + 1}/{max_attempts}")
        
        # 修复失败
        self.logger.logger.warning("所有修复尝试均失败")
        return initial_result
    
    def _execute_subgraph(self, task_graph: dict, subgraph_nodes: list) -> dict:
        """
        执行子图
        
        Args:
            task_graph: 完整任务图
            subgraph_nodes: 需要执行的节点ID列表
            
        Returns:
            执行结果
        """
        # 创建子图
        subgraph = {
            "task_id": task_graph.get("task_id") + "_subgraph",
            "nodes": [n for n in task_graph["nodes"] if n["id"] in subgraph_nodes],
            "edges": [e for e in task_graph["edges"] if e[0] in subgraph_nodes and e[1] in subgraph_nodes],
            "metadata": task_graph.get("metadata", {})
        }
        
        # 执行子图
        return self.executor.execute(subgraph)
    
    def _restore_browser_state(self, browser_state: dict) -> None:
        """
        恢复浏览器状态
        
        Args:
            browser_state: 浏览器状态
        """
        try:
            # 清除当前状态
            self.browser.clear_cookies()
            self.browser.clear_local_storage()
            
            # 恢复cookies
            for cookie in browser_state.get("cookies", []):
                self.browser.set_cookie(cookie)
            
            # 导航到保存的URL
            url = browser_state.get("url")
            if url:
                self.browser.navigate(url)
                
            self.logger.logger.info("浏览器状态已恢复")
        except Exception as e:
            self.logger.logger.error(f"恢复浏览器状态失败: {e}")
    
    def _save_task_graph(self, task_graph: dict) -> None:
        """保存任务图"""
        task_id = task_graph.get("task_id", "unknown")
        # 使用项目根目录
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "results" / "task_graphs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / f"{task_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task_graph, f, indent=2, ensure_ascii=False)
    
    def run_experiment(
        self, 
        experiment_config_path: str = "config/experiment_params.yaml",
        benchmark: str = None,
        num_tasks: int = None
    ):
        """
        运行完整实验
        
        Args:
            experiment_config_path: 实验配置文件路径
            benchmark: 数据集名称 (miniwob, webarena, webchore)，覆盖配置文件
            num_tasks: 任务数量，覆盖配置文件
        """
        # 确保使用项目根目录的路径
        if not Path(experiment_config_path).is_absolute():
            project_root = Path(__file__).parent.parent
            experiment_config_path = project_root / experiment_config_path
        
        # 加载实验配置
        with open(experiment_config_path, 'r', encoding='utf-8') as f:
            exp_config = yaml.safe_load(f)
        
        experiment_name = exp_config.get("experiment", {}).get("name", "experiment")
        benchmark = benchmark or exp_config.get("experiment", {}).get("benchmark", "miniwob")
        num_tasks = num_tasks or exp_config.get("experiment", {}).get("num_tasks", 30)
        
        self.logger.logger.info(f"开始实验: {experiment_name}")
        self.logger.logger.info(f"数据集: {benchmark}")
        self.logger.logger.info(f"任务数量: {num_tasks}")
        
        # 显示Benchmark信息
        benchmark_info = self.data_loader.get_benchmark_info(benchmark)
        if benchmark_info:
            self.logger.logger.info(f"Benchmark: {benchmark_info['name']}")
            self.logger.logger.info(f"描述: {benchmark_info['description']}")
            self.logger.logger.info(f"预计平均步数: {benchmark_info['avg_steps']}")
            self.logger.logger.info(f"预计平均时间: {benchmark_info['avg_time']}")
        
        # 从数据集加载任务
        tasks = self.data_loader.load_tasks(
            benchmark=benchmark,
            split="test",
            num_tasks=num_tasks
        )
        
        if not tasks:
            self.logger.logger.error(f"未能加载任务，请检查数据集: {benchmark}")
            return
        
        self.logger.logger.info(f"成功加载 {len(tasks)} 个任务")
        
        # 运行所有任务
        results = []
        for i, task in enumerate(tasks, 1):
            self.logger.logger.info(f"\n{'='*60}")
            self.logger.logger.info(f"任务 {i}/{len(tasks)}: {task['task_id']}")
            self.logger.logger.info(f"类别: {task.get('category', 'unknown')}")
            self.logger.logger.info(f"难度: {task.get('difficulty', 'unknown')}")
            self.logger.logger.info(f"{'='*60}")
            
            task_instruction = task['instruction']
            start_url = task.get('start_url')
            env_id = task.get('metadata', {}).get('env_id') if isinstance(task.get('metadata'), dict) else None

            # 将数据集上下文附加到任务描述，帮助编译器生成更可执行的图
            context_lines = []
            if env_id:
                context_lines.append(f"环境ID: {env_id}")
            if start_url:
                context_lines.append(f"起始URL: {start_url}")
            if context_lines:
                task_instruction = f"{task_instruction}\n\n" + "\n".join(context_lines)

            result = self.run_task(
                task_instruction,
                task_id=task['task_id']
            )
            
            # 添加任务元数据到结果
            result['task_metadata'] = {
                'category': task.get('category'),
                'difficulty': task.get('difficulty'),
                'benchmark': task.get('benchmark')
            }
            
            results.append(result)
            
            # 短暂休息
            import time
            time.sleep(1)
        
        # 保存实验结果
        self._save_experiment_results(experiment_name, benchmark, results)
    
    def _save_experiment_results(self, experiment_name: str, benchmark: str, results: list):
        """保存实验结果"""
        # 使用数据加载器保存结果
        experiment_id = f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.data_loader.save_results(
            results=results,
            benchmark=benchmark,
            experiment_id=experiment_id,
            variant="full_system"
        )
        
        summary = self.metrics_collector.get_summary()
        
        # 使用项目根目录
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "results" / "performance"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_dir / f"{experiment_name}_{timestamp}.json"
        
        self.metrics_collector.save_metrics(str(filepath))
        
        # 打印摘要
        self.logger.logger.info("\n" + "="*60)
        self.logger.logger.info("实验结果摘要")
        self.logger.logger.info("="*60)
        self.logger.logger.info(f"总任务数: {summary['total_tasks']}")
        self.logger.logger.info(f"成功率: {summary['success_rate']:.2%}")
        self.logger.logger.info(f"平均步数: {summary['avg_steps']:.1f}")
        self.logger.logger.info(f"平均LLM调用: {summary['avg_llm_calls']:.1f}")
        self.logger.logger.info(f"每次成功成本: ${summary['cost_per_success']:.4f}")
        self.logger.logger.info(f"平均修复深度: {summary['avg_repair_depth']:.1f}")
        self.logger.logger.info(f"失败分布: {summary['failure_distribution']}")
        self.logger.logger.info("="*60)
    
    def cleanup(self):
        """清理资源"""
        if self.browser:
            self.browser.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Graph Web Agent 实验运行器")
    parser.add_argument("--config", default="config/default_params.yaml", help="配置文件路径")
    parser.add_argument("--experiment", default="config/experiment_params.yaml", help="实验配置文件路径")
    parser.add_argument("--task", help="单个任务描述（用于快速测试）")
    parser.add_argument("--benchmark", choices=["miniwob", "webarena", "webchore"], 
                       help="数据集选择 (miniwob, webarena, webchore)")
    parser.add_argument("--num-tasks", type=int, help="任务数量")
    parser.add_argument("--no-repair", action="store_true", help="禁用修复机制")
    
    args = parser.parse_args()
    
    # 创建实验运行器
    runner = ExperimentRunner(config_path=args.config)
    
    try:
        if args.task:
            # 运行单个任务
            result = runner.run_task(args.task, use_repair=not args.no_repair)
            print("\n任务结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # 运行完整实验
            runner.run_experiment(
                experiment_config_path=args.experiment,
                benchmark=args.benchmark,
                num_tasks=args.num_tasks
            )
    finally:
        runner.cleanup()


if __name__ == "__main__":
    main()


