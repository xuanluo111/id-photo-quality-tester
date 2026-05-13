import { defineConfig } from "@playwright/test";

export default defineConfig({
    testDir: './tests',
    timeout: 30000,
    retries: process.env.CI ? 2 : 1, //CI 环境多一次重试
    use: {
        baseURL: 'http://localhost:3000',
        // 🎯 关键：根据环境自动选择模式
        headless: process.env.CI ? true : false,
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        trace: 'on-first-retry',
    },
    projects: [
        { name: 'chromium', use: { browserName: 'chromium' } },
        { name: 'firefox', use: { browserName: 'firefox' } },
        { name: 'webkit', use: { browserName: 'webkit' } },
    ],
    reporter: [['html', { outputFolder: 'playwright-report' }]],
    // 💡 可选：CI 环境限制并发数
    workers: process.env.CI ? 2 : undefined,
});