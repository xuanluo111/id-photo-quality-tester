import os
import json
import re
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

prompt = """
生成5组证件照测试用例，字段包括：
- image_name: 模拟文件名，如 "good_1.jpg"
- description: 描述图片特征（如 "清晰正面照"）
- expected_quality: "good" 或 "bad"
- expected_score_range: [min, max]

要求覆盖清晰、模糊、过暗、过亮、偏色等情况。
输出纯JSON数组，不要添加任何解释文字。
"""

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    content = response.choices[0].message.content
    print("原始返回内容：")
    print(content)
    print("="*50)
    
    # 尝试移除 Markdown 代码块标记
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'^```\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    
    # 尝试提取 JSON 数组（如果前后有额外文本）
    match = re.search(r'(\[.*\])', content, re.DOTALL)
    if match:
        content = match.group(1)
    
    data = json.loads(content)
    print("生成的测试数据：")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # 保存到文件
    output_path = os.path.join(os.path.dirname(__file__), '..', 'e2e-tests', 'test-data', 'ai_generated_cases.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"数据已保存至 {output_path}")

except Exception as e:
    print(f"错误：{e}")
    # 打印完整响应对象以便调试
    if 'response' in locals():
        print("完整响应：", response)