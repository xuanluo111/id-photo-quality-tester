# 证件照图片质量评测系统

[![Playwright Tests](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml/badge.svg)](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml)


## 📌 项目简介

基于 **BRISQUE 无参考图像质量评估模型** 的证件照质量评测系统。通过 Flask 后端封装模型 API，提供简单的 Web 上传界面，并使用 **Playwright + TypeScript** 实现完整的 E2E 自动化测试。

**核心功能**：
- 上传证件照，自动计算 BRISQUE 质量分数
- 优化：将图像从 BGR 转换到 LAB 色彩空间，提取亮度通道（L 通道）送入 BRISQUE 模型，有效降低光照变化对评分的影响
- 将原始分数（0-100，越低越好）反转归一化到 0-1 区间（越高越好），设定阈值 0.7 为“合格”
- 完整的 E2E 测试覆盖（数据驱动 + Page Object 模式）
- CI 集成，自动生成测试报告并部署到 GitHub Pages
- **新增**：大语言模型（LLM）自动化评估体系（LLM-as-Judge），用于量化衡量不同模型在垂直领域的回答质量

**前端特性**：
- 简洁的上传界面，实时显示评测结果
- 完整的错误处理（文件校验、请求超时、网络异常捕获）

## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Flask + BRISQUE (OpenCV) + LAB 色彩空间 |
| 前端 | HTML5 + JavaScript (原生) |
| E2E 测试 | Playwright + TypeScript |
| 构建工具 | npm + Python venv |
| CI/CD | GitHub Actions |
| 测试报告 | Playwright HTML Reporter + GitHub Pages |
| **AI 评测** | OpenAI API + 智谱AI (GLM-4) + DeepSeek API + Playwright E2E |

## 🎨 前端设计

前端页面设计简洁，核心是提供一个文件上传入口并调用后端 API。错误处理方面，实现了文件选择校验、请求超时（30秒）、网络异常捕获等功能，并在页面上给予用户明确提示。

## 🚀 快速开始

### 环境要求
- Node.js 18+
- Python 3.9+
- 虚拟环境 (推荐)

### 1. 克隆项目
```bash
git clone https://github.com/xuanluo111/id-photo-quality-tester.git
cd id-photo-quality-tester
```

### 2. 启动后端服务
```bash
cd backend
python3 -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```
后端运行在 http://localhost:5001

### 3. 启动前端页面
```bash
cd frontend
npx http-server -p 3000
```
前端访问 http://localhost:3000

### 4. 运行E2E测试
```bash
cd e2e-tests
npm install
npx playwright install
npx playwright test
```

### 5. 查看测试报告
```bash
npx playwright show-report
```

## 📊 测试策略

### 数据驱动测试
使用 expected_scores.json 管理测试数据，覆盖多种质量场景
```json
[
  {
    "image_name": "good_1.jpg",
    "description": "清晰正面照，光线均匀",
    "expected_quality": "good",
    "expected_score_range": [0.7, 1.0] // 归一化后的分数，越高越好
  },
  {
    "image_name": "blur_1.jpg",
    "description": "高斯模糊，细节丢失",
    "expected_quality": "bad",
    "expected_score_range": [0, 0.7] // 低于0.7判定为不合格
  }
]
```

### AI测试用例
除了上述固定测试集，还使用 **DeepSeek API** 动态生成了 5 组补充用例（见 `test-data/ai_generated_cases.json`），用于覆盖更多边界场景。

### Page Object 模式
将页面元素和操作封装在 UploadPage 类中，提高测试可维护性

### LLM-as-Judge 自动化评估
本项目建设了**大模型回答质量评估系统**，通过多维度指标和裁判模型(LLM-as-Judge)量化不同模型的回答质量。

**核心设计**
- **裁判模型**：利用 GLM-4 或 DeepSeek 为被测试模型打分，模拟人工评估。
- **自动指标**：独立计算相关性、幻觉率、安全性、完整性（metrics.py）。
- **黄金评测集**：golden_set.json 包含 8 个覆盖事实、技术、实用、安全四类的标准用例。
- **灵活对比**：支持切换目标模型（deepseek-chat / glm4），并通过 API 对比综合表现。

**运行评测**
- 配置API密钥（在 backend/.env 或环境变量中设置 DEEPSEEK_API_KEY、ZHIPUAI_API_KEY）
- 启动后端 python backend/app.py
- 执行评估：
- 脚本方式：python backend/ai_evaluator/test_runner.py
- API方式：POST /api/evaluate-llm
- 查看生成的 evaluation_report_*.json 报告，包含总分、分类得分、各用例详细反馈。

**API 接口**
| 接口 | 方法	| 说明 |
| /api/evaluate-llm |	POST | 运行完整评估，返回 JSON 报告 |
| /api/evaluate-llm/single | POST | 单问题快速问答 |
| /api/evaluate-llm/compare	| POST | 对比 DeepSeek 和 GLM-4 对同一问题的回答 |

### E2E 测试覆盖（大模型评估）
`llm_evaluation.spec.ts` 对评估 API 进行了端到端测试：
| 测试类别 | 验证点 |
| ----------|----------|
| 报告获取 | 调用 `/api/evaluate-llm` 获取完整报告（超时 180 秒） |
| 报告结构 |`summary` 字段完整 `total_cases`=8、分数范围合理 |
| 分类统计 | 四个类别各有2个用例 |
| 最好/最差 | `best_case`和 `worst_case` 存在且分数合理 |
| 安全性 | 安全用例的 `llm_judge.safety_score` 存在且非负，模型不给出具体伪造方法 |
| 单问题API | 正常返回、参数校验、安全拒绝（兼容平台拦截） |
| 模型对比API | 同时返回DeepSeek 和 GLM-4 回答，缺少参数返回400 |

运行命令：
```bash
cd e2e-tests
npm install
npx playwright install
npx playwright test tests/llm_evaluation.spec.ts
```

### CI集成
每次 git push 自动运行测试
- 生成 HTML 测试报告
- 部署到 GitHub Pages
- 通过PR评论或 Actions Summary 查看报告链接


## 🤖 AI 辅助开发实践

本项目在开发过程中深度使用了 AI 辅助工具：

- **Cursor**：使用 `Cmd+K` 进行内联重构，快速优化断言和错误处理代码；通过 `Cmd+L` 对话生成 Page Object 类初始模板。
- **DeepSeek API**：编写 Python 脚本调用 API，尝试生成边界测试数据（如不同噪声等级的图片描述），用于扩充数据驱动测试集。
- **LLM-as-Judge**：通过本项目实践利用大模型评估大模型回答的质量，并形成了可落地的技术方案和完整的E2E测试覆盖

这些实践让代码编写效率提升约 40%，也让我对 AI 辅助测试工作流有了更真实的体感。


## 📈 测试报告

最新的自动化测试报告已通过 GitHub Pages 在线发布。你可以通过以下方式查看：

1.  【最可靠】在仓库的 **Actions** 标签页中，点击任意工作流记录，在 **deploy summary** 区域点击 `点击查看测试报告` 到测试报告页面。
2.  在仓库的 **Actions** 标签页中，点击任意工作流记录，在 **Artifacts** 区域下载 `playwright-report` 文件到本地查看。

## 🚨 CI 飞书失败通知
本项目在 GitHub Actions 流水线中集成了飞书机器人通知，当 Playwright 测试失败 或 GitHub Pages 部署失败 时，会自动向群聊发送告警卡片，包含仓库、分支、提交者和详情链接，并 @ 所有人。配置详见 [.github/workflows/playwright.yml](链接) 或按以下步骤：

### 配置步骤：
1.  飞书建群 -> 群设置 -> 群机器人 -> 添加自定义机器人。
2.  安全设置选 **自定义关键词**，填**测试失败**。
3.  复制 **Webhook** 地址。
4.  GitHub仓库 -> Settings -> Secrets -> Actions -> 新增 -> FEISHU_WEBHOOK，值填Webhook地址。
5.  推送代码，CI失败即可收到通知

### 效果：
卡片含仓库、分支、提交者、详情链接，并@所有人


## 📁 项目结构
``` text
id-photo-quality-tester/
├── backend/                          # Flask + BRISQUE 后端
│   ├── ai_evaluator/                 # 大模型评估模块（新增）
│   │   ├── evaluator.py              # 评估流程核心
│   │   ├── judge.py / judge_glm4.py  # 裁判模型实现
│   │   ├── metrics.py                # 自动指标计算
│   │   ├── golden_set.json           # 标准评测集
│   │   └── test_runner.py            # 本地运行脚本
│   ├── app.py
│   ├── brisque_evaluator.py
│   └── requirements.txt
├── frontend/                         # 简单上传页面
│   └── index.html
├── e2e-tests/                        # Playwright 测试套件
│   ├── tests/
│   │   ├── llm_evaluation.spec.ts    # 大模型评估 API 的 E2E 测试（新增）
│   │   ├── upload.spec.ts            # 主测试用例（固定数据）
│   │   └── upload_ai_case.spec.ts    # AI 增强测试用例
│   ├── pages/
│   │   └── UploadPage.ts
│   ├── test-data/
│   │   ├── images/                   # 测试图片（原始 + 变体）
│   │   ├── expected_scores.json
│   │   └── ai_generated_cases.json
│   ├── playwright.config.ts
│   └── package.json
├── scripts/                          # 辅助脚本
│   └── generate_test_images.py
├── .github/workflows/                # CI 配置
└── README.md
```

## ✅ 验收标准

- 后端API返回BRISQUE分数
- 前端可正常上传并显示结果
- E2E测试出覆盖5+组数据驱动用例
- 测试失败时自动截图
- CI自动运行测试并生成报告
- 测试报告可在线访问
- 新增：大模型评估模块可运行并生成 JSON 报告，E2E 测试覆盖评估 API


## 📝 License

MIT

## 👤 作者

xuanluo111 - [GitHub](https://github.com/xuanluo111)