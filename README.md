# 证件照图片质量评测系统

[![Playwright Tests](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml/badge.svg)](https://github.com/xuanluo111/id-photo-quality-tester/actions/workflows/playwright.yml)

## 📌 项目简介

基于 **BRISQUE 无参考图像质量评估模型** 的证件照质量评测系统。通过 Flask 后端封装模型 API，提供简单的 Web 上传界面，并使用 **Playwright + TypeScript** 实现完整的 E2E 自动化测试。

**核心功能**：
- 上传证件照，自动计算 BRISQUE 质量分数
- 分数越低代表质量越差，阈值 0.7 判定为“合格”
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
