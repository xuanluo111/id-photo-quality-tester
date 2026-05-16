# backend/ai_evaluator/evaluator.py
import json
import os
import traceback
from typing import Dict, List
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

from .judge import DeepSeekJudge
from .metrics import QualityMetrics

load_dotenv()


class AIResponseEvaluator:
    """大模型回答质量评估器"""

    def __init__(self, target_model: str = "deepseek-chat"):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")

        self.target_client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.target_model = target_model
        self.metrics = QualityMetrics()
        self.judge = DeepSeekJudge()
        self.golden_set = self._load_golden_set()

    def _load_golden_set(self) -> Dict:
        golden_path = os.path.join(os.path.dirname(__file__), "golden_set.json")
        with open(golden_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def call_target_model(self, question: str) -> str:
        """调用被评估的大模型获取回答"""
        try:
            response = self.target_client.chat.completions.create(
                model=self.target_model,
                messages=[
                    {"role": "system",
                     "content": "你是一个证件照质量评估专家助手，请根据你的知识提供准确、有帮助的回答。"},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"模型调用失败: {str(e)}"

    def evaluate_single_case(self, test_case: Dict, run_times: int = 1) -> Dict:
        """评估单个测试用例"""
        question = test_case["question"]
        context = test_case.get("context", "")
        golden_answer = test_case["golden_answer"]
        key_points = test_case.get("key_points", [])
        forbidden_words = test_case.get("forbidden_words", [])

        print(f"    问题: {question[:50]}...")

        # 运行多次获取回答
        answers = []
        for i in range(run_times):
            answer = self.call_target_model(question)
            answers.append(answer)

        primary_answer = answers[0]

        # 1. 自动指标计算
        print("    计算自动指标...")
        relevance = self.metrics.relevance(primary_answer, key_points)
        hallucination = self.metrics.hallucination_rate(primary_answer, golden_answer, forbidden_words)
        safety = self.metrics.safety(primary_answer)
        completeness = self.metrics.completeness(primary_answer, golden_answer)
        consistency = self.metrics.consistency(answers) if run_times > 1 else 1.0

        # 2. LLM-as-Judge 打分
        print("    调用 LLM Judge...")
        judge_result = self.judge.evaluate(
            question=question,
            answer=primary_answer,
            golden_answer=golden_answer,
            context=context,
        )

        # 3. 综合分数计算（修正版）
        # 自动总分 = 相关性(最高3分) + 准确性(最高4分) + 完整性(最高2分) + 安全性(最高1分)
        # 其中准确性 = 1 - hallucination_rate
        auto_total = (
                relevance * 3 +  # 相关性 0-3
                (1 - hallucination) * 4 +  # 准确性 0-4
                completeness * 2 +  # 完整性 0-2
                safety * 1  # 安全性 0-1
        )
        auto_total = min(10, max(0, auto_total))  # 限制在 0-10

        # 最终得分 = 自动评分40% + LLM评委分60%
        final_score = auto_total * 0.4 + judge_result["total_score"] * 0.6
        final_score = round(min(10, max(0, final_score)), 1)

        print(f"    自动分: {auto_total:.1f}, 评委分: {judge_result['total_score']:.1f}, 最终: {final_score:.1f}")

        return {
            "test_case_id": test_case["id"],
            "category": test_case["category"],
            "difficulty": test_case.get("difficulty", "medium"),
            "question": question,
            "primary_answer": primary_answer[:500],
            "all_answers": answers if run_times > 1 else None,
            "auto_metrics": {
                "relevance_score": round(relevance, 2),
                "hallucination_rate": round(hallucination, 2),
                "safety_score": round(safety, 2),
                "completeness_score": round(completeness, 2),
                "consistency_score": round(consistency, 2) if run_times > 1 else None,
                "auto_total_score": round(auto_total, 1)
            },
            "llm_judge": {
                "relevance_score": judge_result["relevance_score"],
                "accuracy_score": judge_result["accuracy_score"],
                "completeness_score": judge_result["completeness_score"],
                "safety_score": judge_result["safety_score"],
                "total_score": judge_result["total_score"],
                "detailed_feedback": judge_result.get("detailed_feedback", ""),
                "suggestions": judge_result.get("suggestions", "")
            },
            "final_score": final_score,
            "evaluated_at": datetime.now().isoformat()
        }

    def run_full_evaluation(self, run_times: int = 1) -> Dict:
        """运行完整的评估套件"""
        results = []

        for i, test_case in enumerate(self.golden_set["test_cases"], 1):
            print(
                f"评估测试用例 [{i}/{len(self.golden_set['test_cases'])}]: {test_case['id']} - {test_case['category']}")
            try:
                result = self.evaluate_single_case(test_case, run_times)
                results.append(result)
                print(f"  ✅ 完成，得分: {result['final_score']}/10")
            except Exception as e:
                print(f"  ❌ 评估失败: {e}")
                traceback.print_exc()
                results.append({
                    "test_case_id": test_case["id"],
                    "category": test_case["category"],
                    "error": str(e),
                    "final_score": 0
                })

        if not results:
            print("❌ 没有任何测试用例成功执行")
            return {"error": "没有成功执行的测试用例"}

        return self._generate_summary(results)

    def _generate_summary(self, results: List[Dict]) -> Dict:
        """生成汇总报告"""
        # 过滤掉错误的结果
        valid_results = [r for r in results if "error" not in r]

        if not valid_results:
            return {"error": "没有有效的测试结果"}

        total_cases = len(valid_results)

        # 整体平均分
        avg_final_score = sum(r["final_score"] for r in valid_results) / total_cases
        avg_auto_score = sum(r["auto_metrics"]["auto_total_score"] for r in valid_results) / total_cases
        avg_judge_score = sum(r["llm_judge"]["total_score"] for r in valid_results) / total_cases

        # 各维度平均分
        avg_relevance = sum(r["auto_metrics"]["relevance_score"] for r in valid_results) / total_cases
        avg_hallucination = sum(r["auto_metrics"]["hallucination_rate"] for r in valid_results) / total_cases
        avg_safety = sum(r["auto_metrics"]["safety_score"] for r in valid_results) / total_cases
        avg_completeness = sum(r["auto_metrics"]["completeness_score"] for r in valid_results) / total_cases

        # 按类别统计
        category_stats = {}
        difficulty_stats = {}

        for r in valid_results:
            # 按类别
            cat = r["category"]
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "total_score": 0}
            category_stats[cat]["count"] += 1
            category_stats[cat]["total_score"] += r["final_score"]

            # 按难度
            diff = r["difficulty"]
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {"count": 0, "total_score": 0}
            difficulty_stats[diff]["count"] += 1
            difficulty_stats[diff]["total_score"] += r["final_score"]

        # 计算平均分
        for cat in category_stats:
            category_stats[cat]["avg_score"] = round(
                category_stats[cat]["total_score"] / category_stats[cat]["count"], 1
            )

        for diff in difficulty_stats:
            difficulty_stats[diff]["avg_score"] = round(
                difficulty_stats[diff]["total_score"] / difficulty_stats[diff]["count"], 1
            )

        sorted_results = sorted(valid_results, key=lambda r: r["final_score"], reverse=True)

        return {
            "summary": {
                "total_cases": total_cases,
                "avg_final_score": round(avg_final_score, 1),
                "avg_auto_score": round(avg_auto_score, 1),
                "avg_judge_score": round(avg_judge_score, 1),
                "dimension_scores": {
                    "relevance": round(avg_relevance * 10, 1),
                    "hallucination_free": round((1 - avg_hallucination) * 10, 1),
                    "safety": round(avg_safety * 10, 1),
                    "completeness": round(avg_completeness * 10, 1)
                }
            },
            "category_breakdown": category_stats,
            "difficulty_breakdown": difficulty_stats,
            "best_case": {
                "id": sorted_results[0]["test_case_id"],
                "score": sorted_results[0]["final_score"]
            },
            "worst_case": {
                "id": sorted_results[-1]["test_case_id"],
                "score": sorted_results[-1]["final_score"]
            },
            "detailed_results": valid_results,
            "generated_at": datetime.now().isoformat()
        }

    def export_report(self, output_path: str = "evaluation_report.json"):
        """导出评估报告到文件"""
        report = self.run_full_evaluation()
        if report and "error" not in report:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"报告已导出到: {output_path}")
        return report