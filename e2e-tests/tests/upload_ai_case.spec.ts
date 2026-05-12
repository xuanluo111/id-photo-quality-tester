import path from "path";
import { expect, test } from "@playwright/test";
import { captureFullPageFailureShot } from "../helpers/failureScreenshot";
import testData from "../test-data/ai_generated_cases.json";
import { UploadPage } from "../pages/UploadPage";

/** AI 用例失败截图子目录（位于 e2e-tests/test-results 下） */
const AI_CASE_FAILURE_SUBFOLDER = "ai-case-failures";

/** 结果区渲染较慢时（大图或冷启动）拉长等待上限 */
const RESULT_VISIBLE_TIMEOUT_MS = 100_000;

test.describe("证件照质量评估 E2E — AI 生成用例", () => {
    let uploadPage: UploadPage;

    test.beforeEach(async ({ page }) => {
        // 每个用例独立 Page；UploadPage 负责打开首页
        uploadPage = new UploadPage(page);
        try {
            await uploadPage.goto();
        } catch (err) {
            await captureFullPageFailureShot(
                page,
                AI_CASE_FAILURE_SUBFOLDER,
                "beforeEach-goto"
            );
            console.error("[upload_ai_case] beforeEach goto 失败:", err);
            throw err;
        }
    });

    for (const data of testData) {
        test(`上传图片 ${data.image_name}，预期质量: ${data.expected_quality}`, async ({
            page,
        }) => {
            const caseTag = data.image_name;

            try {
                // Fixture 图片目录（与 spec 同级的 test-data/images）
                const imageFixtureDir = path.resolve(
                    __dirname,
                    "../test-data/images"
                );
                const filePath = path.join(imageFixtureDir, data.image_name);

                // 选文件并触发评测
                await uploadPage.uploadImage(filePath);

                // 结果面板：与断言语义绑定，避免重复链式 locator
                const resultPanel = uploadPage.resultDiv;
                await expect(resultPanel).toBeVisible({
                    timeout: RESULT_VISIBLE_TIMEOUT_MS,
                });

                const quality = await uploadPage.getQuality();
                expect(quality).toBe(data.expected_quality);

                const score = await uploadPage.getScore();
                const [minScore, maxScore] = data.expected_score_range;
                expect(score).toBeGreaterThan(minScore);
                expect(score).toBeLessThan(maxScore);
            } catch (err) {
                await captureFullPageFailureShot(
                    page,
                    AI_CASE_FAILURE_SUBFOLDER,
                    caseTag
                );
                console.error(`[upload_ai_case] 用例失败: ${caseTag}`, err);
                throw err;
            }
        });
    }
});
