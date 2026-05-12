# 证件照图片质量评测系统

[![Playwright Tests](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml/badge.svg)](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml)

## 📌 项目简介

基于 **BRISQUE 无参考图像质量评估模型** 的证件照质量评测系统。通过 Flask 后端封装模型 API，提供简单的 Web 上传界面，并使用 **Playwright + TypeScript** 实现完整的 E2E 自动化测试。

**核心功能**：
- 上传证件照，自动计算 BRISQUE 质量分数
- 封装 OpenCV 进行预处理，**包括将图像从 BGR 转换到 LAB 色彩空间，并提取亮度通道（L 通道）** 送入 BRISQUE 模型。这一优化能**有效降低光照变化对评分的影响**，使评估结果更稳定。为了让业务更好理解，将原始分数（0-100，越低越好）反转归一化到 0-1 区间（越高越好），并设定 **阈值 0.7 为“合格”**。
- 完整的 E2E 测试覆盖（数据驱动 + Page Object 模式）
- CI 集成，自动生成测试报告并部署到 GitHub Pages

**前端特性**：
  * 简洁的上传界面，实时显示评测结果
  * 完整的错误处理（文件校验、请求超时、网络异常捕获）
  
## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Flask + BRISQUE (OpenCV) (LAB 色彩空间) |
| 前端 | HTML5 + JavaScript (原生) |
| E2E测试 | Playwright + TypeScript |
| 构建工具 | npm + Python venv |
| CI/CD | GitHub Actions |
| 测试报告 | Playwright HTML Reporter + GitHub Pages |

## 🎨 前端设计

前端页面设计简洁，核心是提供一个文件上传入口并调用后端 API。**错误处理方面，实现了文件选择校验、请求超时（30秒）、网络异常捕获等功能**，并在页面上给予用户明确提示。

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

### CI集成
每次 git push 自动运行测试
- 生成 HTML 测试报告
- 部署到 GitHub Pages
- 通过PR评论或 Actions Summary 查看报告链接

## 🤖 AI 辅助开发实践

本项目在开发过程中深度使用了 AI 辅助工具：

- **Cursor**：使用 `Cmd+K` 进行内联重构，快速优化断言和错误处理代码；通过 `Cmd+L` 对话生成 Page Object 类初始模板。
- **DeepSeek API**：编写 Python 脚本调用 API，尝试生成边界测试数据（如不同噪声等级的图片描述），用于扩充数据驱动测试集。

这些实践让代码编写效率提升约 40%，也让我对 AI 辅助测试工作流有了更真实的体感。

## 📈 测试报告

最新的自动化测试报告已通过 GitHub Pages 在线发布。你可以通过以下方式查看：

1.  【最可靠】在仓库的 **Actions** 标签页中，点击任意工作流记录，在 **deploy summary** 区域点击 `点击查看测试报告` 到测试报告页面。
2.  在仓库的 **Actions** 标签页中，点击任意工作流记录，在 **Artifacts** 区域下载 `playwright-report` 文件到本地查看。

## 📁 项目结构
``` text
id-photo-quality-tester/
├── backend/                        # Flask + BRISQUE 后端
│   ├── app.py
│   ├── brisque_evaluator.py
│   └── requirements.txt
├── frontend/                       # 简单上传页面
│   └── index.html
├── e2e-tests/                      # Playwright 测试套件
│   ├── tests/
│   │   └── upload.spec.ts          # 主测试用例（固定数据）
│   │   └── upload_ai_case.spec.ts  # AI 增强测试用例
│   ├── pages/
│   │   └── UploadPage.ts
│   ├── test-data/
│   │   ├── images/                 # 测试图片（原始 + 变体）
│   │   └── expected_scores.json
│   │   └── ai_generated_cases.json
│   ├── playwright.config.ts
│   └── package.json
├── scripts/                        # 辅助脚本
│   └── generate_test_images.py
├── .github/workflows/              # CI 配置
└── README.md
```

## ✅ 验收标准

- 后端API返回BRISQUE分数
- 前端可正常上传并显示结果
- E2E测试出覆盖5+组数据驱动用例
- 测试失败时自动截图
- CI自动运行测试并生成报告
- 测试报告可在线访问

## 📝 License

MIT

## 👤 作者

xuanluo111 - [GitHub](https://github.com/xuanluo111)