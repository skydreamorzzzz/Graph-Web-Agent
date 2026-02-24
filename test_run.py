#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试运行脚本"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "scripts"))

# 测试导入
try:
    from run_experiment import ExperimentRunner
    print("[OK] ExperimentRunner 导入成功")
    
    # 测试初始化
    runner = ExperimentRunner()
    print("[OK] ExperimentRunner 初始化成功")
    
    # 测试运行任务
    print("\n开始运行测试任务...")
    result = runner.run_task("访问example.com并提取标题", use_repair=False)
    
    print("\n任务结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  步数: {result.get('steps')}")
    print(f"  耗时: {result.get('duration', 0):.2f}秒")
    
    if not result.get('success'):
        print(f"  错误: {result.get('error')}")
    
    runner.cleanup()
    print("\n[OK] 测试完成")
    
except Exception as e:
    print(f"[ERROR] 错误: {e}")
    import traceback
    traceback.print_exc()
