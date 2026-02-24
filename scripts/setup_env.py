#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从系统环境变量创建 .env 文件"""

import os

# 从系统环境变量读取
deepseek_key = os.environ.get("DEEPSEEK_API_KEY")

if deepseek_key:
    # 写入 .env 文件
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"DEEPSEEK_API_KEY={deepseek_key}\n")
    print(f"[OK] 已创建 .env 文件")
    print(f"[OK] 密钥长度: {len(deepseek_key)} 字符")
    print(f"[OK] 密钥前缀: {deepseek_key[:10]}...")
else:
    print("[ERROR] 环境变量 DEEPSEEK_API_KEY 未找到")
    print("\n请先设置环境变量，然后重启终端：")
    print('[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-your-key", "User")')

