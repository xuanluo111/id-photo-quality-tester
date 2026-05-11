# 证件照图片质量评测系统

[![Playwright Tests](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml/badge.svg)](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml)

## 📌 项目简介

基于 **BRISQUE 无参考图像质量评估模型** 的证件照质量评测系统。通过 Flask 后端封装模型 API，提供简单的 Web 上传界面，并使用 **Playwright + TypeScript** 实现完整的 E2E 自动化测试。

**核心功能**：
- 上传证件照，自动计算 BRISQUE 质量分数
- **原始 BRISQUE 分数（0-100）越低越好**，后端将其**反转归一化**为 0-1 区间（越高越好）
- **最终分数 > 0.7 判定为“合格”**
- 完整的 E2E 测试覆盖（数据驱动 + Page Object 模式）
- CI 集成，自动生成测试报告并部署到 GitHub Pages

## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | Flask + BRISQUE (OpenCV) |
| 前端 | HTML5 + JavaScript (原生) |
| E2E测试 | Playwright + TypeScript |
| 构建工具 | npm + Python venv |
| CI/CD | GitHub Actions |
| 测试报告 | Playwright HTML Reporter + GitHub Pages |

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

### Page Object 模式
将页面元素和操作封装在 UploadPage 类中，提高测试可维护性

### CI集成
每次 git push 自动运行测试
- 生成 HTML 测试报告
- 部署到 GitHub Pages
- 通过PR评论或 Actions Summary 查看报告链接

## 📈 测试报告

最新的自动化测试报告已通过 GitHub Pages 在线发布。你可以通过以下方式查看：

1.  在仓库的 **Actions** 标签页中，点击任意工作流记录，在 **deploy summary** 区域点击 `点击查看测试报告` 到测试报告页面。
2.  在仓库的 **Actions** 标签页中，点击任意工作流记录，在 **Artifacts** 区域下载 `playwright-report` 文件到本地查看。

## 📁 项目结构
``` text
id-photo-quality-tester/
├── backend/               # Flask + BRISQUE 后端
│   ├── app.py
│   ├── brisque_evaluator.py
│   └── requirements.txt
├── frontend/              # 简单上传页面
│   └── index.html
├── e2e-tests/             # Playwright 测试套件
│   ├── tests/
│   │   └── upload.spec.ts
│   ├── pages/
│   │   └── UploadPage.ts
│   ├── test-data/
│   │   ├── images/        # 测试图片（原始 + 变体）
│   │   └── expected_scores.json
│   ├── playwright.config.ts
│   └── package.json
├── scripts/               # 辅助脚本
│   └── generate_test_images.py
├── .github/workflows/     # CI 配置
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