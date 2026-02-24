"""
Graph-Compiled Web Agent

一个基于任务图编译、局部修复和成本感知路由的结构化 Web Agent 研究项目。
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your-email@example.com"

from .task_compiler.compiler import TaskCompiler
from .task_compiler.validator import GraphValidator
from .graph_executor.executor import GraphExecutor
from .graph_executor.dual_verifier import DualVerifier
from .local_repair.repair import LocalRepairEngine
from .local_repair.rollback import RollbackManager
from .router.router import CostAwareRouter
from .models.browser_env import PlaywrightBrowser

__all__ = [
    "TaskCompiler",
    "GraphValidator",
    "GraphExecutor",
    "DualVerifier",
    "LocalRepairEngine",
    "RollbackManager",
    "CostAwareRouter",
    "PlaywrightBrowser",
]


