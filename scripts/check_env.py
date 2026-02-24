#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查环境变量"""

import os
import sys

print("=" * 60)
print("检查环境变量")
print("=" * 60)

# 检查 DEEPSEEK_API_KEY
deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
if deepseek_key:
    print(f"[OK] DEEPSEEK_API_KEY: {deepseek_key[:10]}...")
else:
    print("[SKIP] DEEPSEEK_API_KEY 未设置")

# 检查 QWEN_API_KEY
qwen_key = os.environ.get("QWEN_API_KEY")
if qwen_key:
    print(f"[OK] QWEN_API_KEY: {qwen_key[:10]}...")
else:
    print("[SKIP] QWEN_API_KEY 未设置")

print("\n提示：")
print("如果环境变量未显示，请：")
print("1. 重启终端/PowerShell")
print("2. 或者创建 .env 文件：")
print("   echo DEEPSEEK_API_KEY=sk-your-key > .env")

