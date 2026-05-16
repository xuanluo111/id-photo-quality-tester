#!/usr/bin/env python3
"""单独测试一个用例，便于调试"""
import os.path
import sys
import traceback

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_evaluator.evaluator import AIResponseEvaluator

# 加载环境变量
load_dotenv()

# 检查API key
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("❌ 请先设置 DEEPSEEK_API_KEY 环境变量")
    print("  export DEEPSEEK_API_KEY='your_key'")
    sys.exit(1)

print(f"✅ API Key 已设置: {api_key[:10]}...")

def test_single_case():
    print("\n开始测试单个用例...")

    try:
        evaluator = AIResponseEvaluator()

        # 只测试第一个用例
        test_case = evaluator.golden_set["test_cases"][0]
        print(f"测试用例：{test_case['id']}")
        print(f"问题：{test_case['question']}")

        result = evaluator.evaluate_single_case(test_case, run_times=1)
        print(f"\n✅ 评估完成!")
        print(f"最终得分：{result['final_score']}/10")
        print(f"模型回答：{result['primary_answer'][:200]}...")

        return result
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_single_case()
