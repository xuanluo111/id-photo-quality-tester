import path from "path";
import { expect, test } from "@playwright/test";
import { captureFullPageFailureShot } from "../helpers/failureScreenshot";
import testData from "../test-data/expected_scores.json";
import { UploadPage } from "../pages/UploadPage";

/** 普通用例失败截图子目录 */
const UPLOAD_SPEC_FAILURE_SUBFOLDER = "upload-spec-failures";

/** 默认等待结果区出现的最长时间（毫秒） */
const RESULT_VISIBLE_TIMEOUT_MS = 10_000;

/** Fixture 图片根目录 */
const IMAGE_FIXTURE_DIR = path.resolve(__dirname, "../test-data/images");

test.describe("证件照质量评估 E2E", () => {
    let uploadPage: UploadPage;

    test.beforeEach(async ({ page }) => {
        uploadPage = new UploadPage(page);
        try {
            await uploadPage.goto();
        } catch (err) {
            await captureFullPageFailureShot(
                page,
                UPLOAD_SPEC_FAILURE_SUBFOLDER,
                "beforeEach-goto"
            );
            console.error("[upload.spec] beforeEach goto 失败:", err);
            throw err;
        }
    });

    for (const data of testData) {
        test(`上传图片 ${data.image}，预期质量: ${data.expectedQuality}`, async ({
            page,
        }) => {
            const caseTag = data.image;

            try {
                const filePath = path.join(IMAGE_FIXTURE_DIR, data.image);
                await uploadPage.uploadImage(filePath);

                const resultPanel = uploadPage.resultDiv;
                await expect(resultPanel).toBeVisible({
                    timeout: RESULT_VISIBLE_TIMEOUT_MS,
                });

                const quality = await uploadPage.getQuality();
                expect(quality).toBe(data.expectedQuality);

                const score = await uploadPage.getScore();
                if (data.maxScore !== undefined) {
                    expect(score).toBeGreaterThan(data.maxScore);
                }
                if (data.minScore !== undefined) {
                    expect(score).toBeLessThan(data.minScore);
                }
            } catch (err) {
                await captureFullPageFailureShot(
                    page,
                    UPLOAD_SPEC_FAILURE_SUBFOLDER,
                    caseTag
                );
                console.error(`[upload.spec] 用例失败: ${caseTag}`, err);
                throw err;
            }
        });
    }
});
