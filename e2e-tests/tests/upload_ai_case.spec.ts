import { test, expect } from "@playwright/test";
import { UploadPage } from "../pages/UploadPage";
import testData from "../test-data/ai_generated_cases.json";
import path from "path"

test.describe('证件照质量评估E2E测试-ai生成的测试数据', () => {
    let uploadPage: UploadPage;

    test.beforeEach(async ({ page }) => {
        uploadPage = new UploadPage(page);
        await uploadPage.goto();
    });

    for (const data of testData) {
        test(`上传图片 ${data.image_name}，预期质量: ${data.expected_quality}`, async () => {
            const filePath = path.resolve(__dirname, '../test-data/images', data.image_name);
            await uploadPage.uploadImage(filePath);

            //等待结果显示
            await expect(uploadPage.resultDiv).toBeVisible({ timeout: 100000 });
            const quality = await uploadPage.getQuality();
            expect(quality).toBe(data.expected_quality);

            //可选：验证分数范围
            const score = await uploadPage.getScore();
            const [minScore, maxScore] = data.expected_score_range;
            expect(score).toBeGreaterThan(minScore);
            expect(score).toBeLessThan(maxScore);
        }); 
    }
});