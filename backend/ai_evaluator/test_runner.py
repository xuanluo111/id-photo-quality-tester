#!/usr/bin/env python3
"""
独立运行大模型评估
使用方法: python -m backend.ai_evaluator.test_runner
"""
import os
import sys
import json
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_evaluator.evaluator import AIResponseEvaluator

def main():
    print("=" * 60)
    print("🤖 大模型回答质量评估系统")
    print("=" * 60)

    try:
        # 初始化评估器
        print("\n1. 初始化评估器...")
        evaluator = AIResponseEvaluator(target_model="glm4", judge_type="glm4")
        print("   ✅ 评估器初始化成功")

        # 运行完整评估
        print("\n2. 开始评估（这可能需要1-2分钟）...")
        report = evaluator.run_full_evaluation(run_times=1)

        # 检查返回值
        if report is None or "error" in report:
            print(f"   ❌ 评估失败: {report.get('error', '未知错误')}")
            return

        print("   ✅ 评估完成")

        # 打印总结
        print("\n" + "=" * 60)
        print("📊 评估结果汇总")
        print("=" * 60)

        summary = report["summary"]
        print(f"\n📈 总体情况:")
        print(f"   - 测试用例数: {summary['total_cases']}")
        print(f"   - 综合得分: {summary['avg_final_score']}/10")
        print(f"   - 自动评分: {summary['avg_auto_score']}/10")
        print(f"   - LLM评委分: {summary['avg_judge_score']}/10")

        print(f"\n📐 各维度表现:")
        dims = summary["dimension_scores"]
        print(f"   - 相关性: {dims['relevance']}/10")
        print(f"   - 准确性(无幻觉): {dims['hallucination_free']}/10")
        print(f"   - 安全性: {dims['safety']}/10")
        print(f"   - 完整性: {dims['completeness']}/10")

        print(f"\n📂 按类别统计:")
        for cat, stats in report["category_breakdown"].items():
            print(f"   - {cat}: {stats['avg_score']}/10 ({stats['count']}个用例)")

        print(f"\n📂 按难度统计:")
        for diff, stats in report["difficulty_breakdown"].items():
            print(f"   - {diff}: {stats['avg_score']}/10 ({stats['count']}个)")

        print(f"\n🏆 最佳用例: {report['best_case']['id']} ({report['best_case']['score']}/10)")
        print(f"⚠️  最差用例: {report['worst_case']['id']} ({report['worst_case']['score']}/10)")

        # 打印详细结果摘要
        print(f"\n🔍 详细结果摘要:")
        print("-" * 40)
        for r in report["detailed_results"][:4]:  # 只显示前4个
            print(f"   [{r['test_case_id']}] {r['category']}: {r['final_score']}/10")
            if "llm_judge" in r and "detailed_feedback" in r["llm_judge"]:
                feedback = r["llm_judge"]["detailed_feedback"][:60]
                print(f"       反馈: {feedback}...")

        # 导出详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"evaluation_report_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n💾 详细报告已保存到: {report_file}")

        print("\n✅ 评估完成!")

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()

if __name__ == '__main__':
    main()