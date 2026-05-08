import { test, expect } from "@playwright/test";
import { UploadPage } from "../pages/UploadPage";
import testData from "../test-data/expected_scores.json";
import path from "path";

/** 初始代码
 * test('上传清晰照片应判定为合格', async({ page }) => {
    await page.goto('http://localhost:3000');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-data/images/good.jpg');
    await page.getByRole('button', {name: '评测质量' }).click();
    await expect(page.locator('#result')).toContainText('✅ 合格');
});
 */

test.describe('证件照质量评估E2E测试', () => {
    let uploadPage: UploadPage;

    test.beforeEach(async ({ page }) => {
        uploadPage = new UploadPage(page);
        await uploadPage.goto();
    });

    for (const data of testData) {
        test(`上传图片${data.image}，预期质量: ${data.expectedQuality}`, async () => {
            const filePath = path.join(__dirname, '../test-data/images', data.image);
            await uploadPage.uploadImage(filePath);

            //等待结果显示
            await expect(uploadPage.resultDiv).toBeVisible({ timeout: 10000 });
            const quality = await uploadPage.getQuality();
            expect(quality).toBe(data.expectedQuality);

            //可选： 验证分数范围
            const score = await uploadPage.getScore();
            if (data.maxScore) {
                expect(score).toBeGreaterThan(data.maxScore);
            }
            if (data.minScore){
                expect(score).toBeLessThan(data.minScore);
            }
        });
    }
});
