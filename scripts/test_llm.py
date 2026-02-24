#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试DeepSeek和Qwen配置"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.model_loader import ModelLoader

def test_deepseek():
    """测试DeepSeek"""
    print("\n=== 测试 DeepSeek ===")
    loader = ModelLoader()
    
    if not loader.deepseek_api_key:
        print("[SKIP] DeepSeek API密钥未配置")
        print("请在 .env 文件中添加: DEEPSEEK_API_KEY=sk-your-key")
        return False
    
    try:
        model = loader.load_model("deepseek-chat")
        response = model.generate("请用JSON格式输出一个简单的问候：{'message': 'hello'}")
        print(f"[OK] DeepSeek工作正常")
        print(f"响应: {response[:200]}...")
        return True
    except Exception as e:
        print(f"[ERROR] DeepSeek测试失败: {e}")
        return False

def test_qwen():
    """测试Qwen"""
    print("\n=== 测试 Qwen ===")
    loader = ModelLoader()
    
    if not loader.qwen_api_key:
        print("[SKIP] Qwen API密钥未配置")
        print("请在 .env 文件中添加: QWEN_API_KEY=sk-your-key")
        return False
    
    try:
        model = loader.load_model("qwen-turbo")
        response = model.generate("请用JSON格式输出一个简单的问候：{'message': 'hello'}")
        print(f"[OK] Qwen工作正常")
        print(f"响应: {response[:200]}...")
        return True
    except Exception as e:
        print(f"[ERROR] Qwen测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("测试 DeepSeek 和 Qwen 配置")
    print("=" * 60)
    
    deepseek_ok = test_deepseek()
    qwen_ok = test_qwen()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"DeepSeek: {'[OK] 通过' if deepseek_ok else '[SKIP] 失败或未配置'}")
    print(f"Qwen: {'[OK] 通过' if qwen_ok else '[SKIP] 失败或未配置'}")
    
    if not deepseek_ok and not qwen_ok:
        print("\n提示：")
        print("1. 创建 .env 文件在项目根目录")
        print("2. 添加 API 密钥：")
        print("   DEEPSEEK_API_KEY=sk-your-deepseek-key")
        print("   QWEN_API_KEY=sk-your-qwen-key")
        print("3. 安装依赖：")
        print("   pip install openai python-dotenv")
        print("   pip install dashscope  # 如果使用Qwen")

if __name__ == "__main__":
    main()

