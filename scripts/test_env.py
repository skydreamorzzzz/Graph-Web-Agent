#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试环境变量读取"""

import os
import sys
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("环境变量诊断")
print("=" * 60)

# 方法1: os.environ.get()
deepseek_key_1 = os.environ.get("DEEPSEEK_API_KEY")
print(f"\n方法1 - os.environ.get():")
print(f"  DEEPSEEK_API_KEY = {deepseek_key_1}")

# 方法2: os.getenv()
deepseek_key_2 = os.getenv("DEEPSEEK_API_KEY")
print(f"\n方法2 - os.getenv():")
print(f"  DEEPSEEK_API_KEY = {deepseek_key_2}")

# 方法3: 直接访问 os.environ
try:
    deepseek_key_3 = os.environ["DEEPSEEK_API_KEY"]
    print(f"\n方法3 - os.environ[]:")
    print(f"  DEEPSEEK_API_KEY = {deepseek_key_3}")
except KeyError:
    print(f"\n方法3 - os.environ[]:")
    print(f"  DEEPSEEK_API_KEY = [未找到]")

# 方法4: 使用 python-dotenv
print(f"\n方法4 - python-dotenv:")
try:
    from dotenv import load_dotenv
    print("  [OK] python-dotenv 已安装")
    
    # 检查 .env 文件
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"  [OK] .env 文件存在: {env_file}")
        load_dotenv(env_file)
        deepseek_key_4 = os.getenv("DEEPSEEK_API_KEY")
        print(f"  DEEPSEEK_API_KEY = {deepseek_key_4}")
    else:
        print(f"  [X] .env 文件不存在: {env_file}")
except ImportError:
    print("  [X] python-dotenv 未安装")
    print("  请运行: pip install python-dotenv")

# 打印所有环境变量（查找 DEEPSEEK）
print(f"\n所有包含 'DEEPSEEK' 的环境变量:")
found = False
for key, value in os.environ.items():
    if "DEEPSEEK" in key.upper():
        print(f"  {key} = {value}")
        found = True
if not found:
    print("  [未找到]")

print("\n" + "=" * 60)
print("诊断建议")
print("=" * 60)

if not deepseek_key_1 and not deepseek_key_2:
    print("\n环境变量未读取到，可能的原因：")
    print("1. 设置环境变量后未重启 PowerShell")
    print("2. 环境变量设置在 User 级别，当前进程未刷新")
    print("\n解决方案：")
    print("方案1 - 在当前 PowerShell 会话中设置：")
    print('  $env:DEEPSEEK_API_KEY = "sk-你的密钥"')
    print("\n方案2 - 使用 .env 文件（推荐）：")
    print('  echo "DEEPSEEK_API_KEY=sk-你的密钥" > .env')
    print("\n方案3 - 重启 PowerShell 后再试")
else:
    print("\n[OK] 环境变量读取成功！")
    print(f"  密钥前缀: {deepseek_key_1[:10] if deepseek_key_1 else 'N/A'}...")

