import path from "path";
import { expect, test } from "@playwright/test";
import { captureFullPageFailureShot } from "../helpers/failureScreenshot";
import testData from "../test-data/ai_generated_cases.json";
import { UploadPage } from "../pages/UploadPage";

const AI_CASE_FAILURE_SUBFOLDER = "ai-case-failures";

/** 与 AI 用例、冷启动、模型耗时匹配；传给 uploadImage，与 index.html 长耗时评测一致 */
const EVALUATION_RESULT_TIMEOUT_MS = 100_000;

test.describe("证件照质量评估 E2E — AI 生成用例", () => {
    let uploadPage: UploadPage;

    test.beforeEach(async ({ page }) => {
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
                const imageFixtureDir = path.resolve(
                    __dirname,
                    "../test-data/images"
                );
                const filePath = path.join(imageFixtureDir, data.image_name);

                // UploadPage 会等到 #result 出现「BRISQUE分数」「质量判定」成功模板，再往下断言
                await uploadPage.uploadImage(filePath, {
                    resultTimeoutMs: EVALUATION_RESULT_TIMEOUT_MS,
                });

                const resultPanel = uploadPage.resultDiv;
                await expect(resultPanel).toContainText("BRISQUE分数", {
                    timeout: 5_000,
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
