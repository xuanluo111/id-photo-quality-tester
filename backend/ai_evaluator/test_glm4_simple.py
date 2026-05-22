# test_glm4_simple.py
import os
from openai import OpenAI

api_key = os.getenv("ZHIPUAI_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://open.bigmodel.cn/api/paas/v4/")
prompt = """
请输出JSON：{"score": 8, "feedback": "回答正确"}
"""

try:
    response = client.chat.completions.create(
        model="glm-4-flash",  # 先用免费的测试
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    print("✅ 成功:", response.choices[0].message.content)
except Exception as e:
    print("❌ 失败:", e)