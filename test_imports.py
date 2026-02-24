#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试所有核心模块是否可以正常导入"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("测试模块导入...")

try:
    from graph_executor.executor import GraphExecutor
    print("✓ GraphExecutor 导入成功")
except Exception as e:
    print(f"✗ GraphExecutor 导入失败: {e}")

try:
    from graph_executor.dual_verifier import DualVerifier
    print("✓ DualVerifier 导入成功")
except Exception as e:
    print(f"✗ DualVerifier 导入失败: {e}")

try:
    from local_repair.repair import LocalRepairEngine
    print("✓ LocalRepairEngine 导入成功")
except Exception as e:
    print(f"✗ LocalRepairEngine 导入失败: {e}")

try:
    from local_repair.rollback import RollbackManager, EnvironmentReset, NoProgressDetector
    print("✓ RollbackManager 导入成功")
except Exception as e:
    print(f"✗ RollbackManager 导入失败: {e}")

try:
    from router.router import CostAwareRouter
    print("✓ CostAwareRouter 导入成功")
except Exception as e:
    print(f"✗ CostAwareRouter 导入失败: {e}")

try:
    from task_compiler.compiler import TaskCompiler
    print("✓ TaskCompiler 导入成功")
except Exception as e:
    print(f"✗ TaskCompiler 导入失败: {e}")

try:
    from task_compiler.validator import GraphValidator
    print("✓ GraphValidator 导入成功")
except Exception as e:
    print(f"✗ GraphValidator 导入失败: {e}")

try:
    from models.browser_env import PlaywrightBrowser
    print("✓ PlaywrightBrowser 导入成功")
except Exception as e:
    print(f"✗ PlaywrightBrowser 导入失败: {e}")

print("\n所有核心模块导入测试完成！")


