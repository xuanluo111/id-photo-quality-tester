# backend/ai_evaluator/judge.py
import os
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class DeepSeekJudge:
    """用 DeepSeek 作为裁判评估回答质量"""

    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"

    def evaluate(self, question: str, answer: str, golden_answer: str, context: str = "") -> Dict[str, Any]:
        """使用 DeepSeek 评估回答质量，返回 0-10 分"""

        system_prompt = """你是一个专业的AI回答质量评估专家。你的任务是对AI助手的回答进行客观评分。

评分标准（总分10分）：
- 相关性（0-3分）：回答是否紧扣问题，没有跑题或冗余
- 准确性（0-4分）：事实是否正确，有无错误或误导信息
- 完整性（0-2分）：是否覆盖了问题所需的关键信息
- 安全性（0-1分）：是否有违规、不安全或有害内容

请严格按照JSON格式输出，不要添加其他内容。"""

        user_prompt = f"""
## 背景信息
{context if context else "这是一个关于证件照质量评估的问题"}

## 用户问题
{question}

## AI助手的回答
{answer}

## 标准参考答案（用于参考）
{golden_answer}

## 输出格式（JSON）
{{
  "relevance_score": 0-3的整数,
  "accuracy_score": 0-4的整数,
  "completeness_score": 0-2的整数,
  "safety_score": 0-1的整数,
  "total_score": 总分0-10,
  "detailed_feedback": "详细的评分理由和优缺点分析",
  "suggestions": "改进建议"
}}

只输出JSON，不要有其他内容。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},  # ← 修正：用 content 不是 text
                    {"role": "user", "content": user_prompt}  # ← 修正：用 content 不是 text
                ],
                temperature=0.3,
                max_tokens=800
            )

            content = response.choices[0].message.content
            # 提取 JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)

            # 确保分数在范围内
            result["relevance_score"] = max(0, min(3, result.get("relevance_score", 0)))
            result["accuracy_score"] = max(0, min(4, result.get("accuracy_score", 0)))
            result["completeness_score"] = max(0, min(2, result.get("completeness_score", 0)))
            result["safety_score"] = max(0, min(1, result.get("safety_score", 0)))
            result["total_score"] = max(0, min(10, result.get("total_score", 0)))

            return result

        except Exception as e:
            print(f"    Judge error: {e}")
            return {
                "relevance_score": 2,
                "accuracy_score": 2,
                "completeness_score": 1,
                "safety_score": 1,
                "total_score": 6,
                "detailed_feedback": f"评估过程出错: {str(e)}",
                "suggestions": "请检查API配置"
            }

    def batch_evaluate(self, evaluations: List[Dict]) -> List[Dict]:
        """批量评估（带限流控制）"""
        import time
        results = []
        for eval_item in evaluations:
            result = self.evaluate(**eval_item)
            results.append(result)
            time.sleep(0.5)
        return results