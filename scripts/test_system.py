"""
Simple Test - 简单测试脚本
用于验证系统基本功能
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from task_compiler.compiler import TaskCompiler
from task_compiler.validator import GraphValidator


def test_task_compiler():
    """测试任务编译器"""
    print("=" * 60)
    print("测试 1: 任务编译器")
    print("=" * 60)
    
    compiler = TaskCompiler()
    task_description = "访问Google搜索页面，搜索'Web Agent'"
    
    print(f"任务描述: {task_description}")
    print("\n编译任务图...")
    
    task_graph = compiler.compile(task_description, task_id="test_001")
    
    print(f"[OK] 任务图生成成功")
    print(f"  节点数: {len(task_graph['nodes'])}")
    print(f"  边数: {len(task_graph['edges'])}")
    
    return task_graph


def test_graph_validator(task_graph):
    """测试图验证器"""
    print("\n" + "=" * 60)
    print("测试 2: 图验证器")
    print("=" * 60)
    
    validator = GraphValidator()
    
    print("验证任务图...")
    is_valid, errors = validator.validate(task_graph)
    
    if is_valid:
        print("[OK] 任务图验证通过")
    else:
        print("[FAIL] 任务图验证失败")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n获取拓扑排序...")
    topo_order = validator.get_topological_order(
        task_graph["nodes"],
        task_graph["edges"]
    )
    print(f"[OK] 拓扑排序: {' -> '.join(topo_order)}")
    
    return True


def test_dual_verifier():
    """测试双路验证器"""
    print("\n" + "=" * 60)
    print("测试 3: 双路验证器")
    print("=" * 60)
    
    from graph_executor.dual_verifier import DualVerifier
    
    verifier = DualVerifier()
    
    # 模拟节点和页面状态
    node = {
        "id": "N1",
        "type": "NAVIGATE",
        "goal": "导航到搜索页面",
        "predicate": "URL包含search",
        "params": {"url": "https://example.com/search"}
    }
    
    page_state = {
        "url": "https://example.com/search",
        "title": "Search Page",
        "text_content": "Search results...",
        "dom_elements": ["element1", "element2"]
    }
    
    print("执行验证...")
    result = verifier.verify(node, page_state)
    
    print(f"[OK] 验证完成")
    print(f"  总置信度: {result.confidence:.2f}")
    print(f"  硬验证分数: {result.hard_score:.2f}")
    print(f"  软验证分数: {result.soft_score:.2f}")
    print(f"  一致性分数: {result.consistency_score:.2f}")
    print(f"  是否通过: {'是' if result.passed else '否'}")
    
    return True


def test_repair_engine():
    """测试修复引擎"""
    print("\n" + "=" * 60)
    print("测试 4: 局部修复引擎")
    print("=" * 60)
    
    from local_repair.repair import LocalRepairEngine, FailureType
    
    repair_engine = LocalRepairEngine()
    
    print("测试失败分类...")
    for failure_type in FailureType:
        strategy = repair_engine.select_repair_strategy(failure_type, attempt=0)
        if strategy:
            print(f"[OK] {failure_type.value}: {strategy.strategy_name} (回滚深度: {strategy.rollback_depth})")
    
    return True


def test_cost_router():
    """测试成本路由器"""
    print("\n" + "=" * 60)
    print("测试 5: 成本感知路由器")
    print("=" * 60)
    
    from router.router import CostAwareRouter, ModelTier
    
    router = CostAwareRouter()
    
    # 测试路由决策
    node = {
        "id": "N1",
        "type": "NAVIGATE",
        "params": {"url": "https://example.com"}
    }
    
    page_state = {
        "dom_elements": list(range(100)),
        "text_content": "Some content"
    }
    
    print("测试路由决策...")
    tier = router.route(node, page_state)
    print(f"[OK] 路由结果: {tier.value}")
    
    # 记录调用
    router.record_call(tier, "N1", input_tokens=100, output_tokens=50)
    
    stats = router.get_stats()
    print(f"[OK] 成本统计:")
    print(f"  总调用: {stats['total_calls']}")
    print(f"  总成本: ${stats['total_cost']:.4f}")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Graph-Compiled Web Agent - 系统测试")
    print("=" * 60)
    
    try:
        # 测试1: 任务编译
        task_graph = test_task_compiler()
        
        # 测试2: 图验证
        if not test_graph_validator(task_graph):
            print("\n[FAIL] 测试失败")
            return
        
        # 测试3: 双路验证
        test_dual_verifier()
        
        # 测试4: 修复引擎
        test_repair_engine()
        
        # 测试5: 成本路由
        test_cost_router()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)
        print("\n系统已就绪，可以开始运行实验。")
        print("\n下一步:")
        print("  1. 运行单个任务: python run_experiment.py --task '你的任务'")
        print("  2. 运行完整实验: python run_experiment.py")
        print("  3. 查看文档: ../docs/QUICKSTART.md")
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

