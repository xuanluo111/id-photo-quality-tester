import fs from "fs";
import path from "path";
import type { Page } from "@playwright/test";

const E2E_ROOT = path.join(__dirname, "..");

/**
 * 失败时保存全页截图到 e2e-tests/test-results/<subfolder>/。
 * 截图过程异常只打日志，不抛出，避免掩盖原始用例错误。
 */
export async function captureFullPageFailureShot(
    page: Page,
    subfolder: string,
    tag: string
): Promise<void> {
    try {
        const dir = path.join(E2E_ROOT, "test-results", subfolder);
        fs.mkdirSync(dir, { recursive: true });
        const safeTag = tag.replace(/[^\w.-]+/g, "_");
        const filePath = path.join(dir, `${safeTag}-${Date.now()}.png`);
        await page.screenshot({ path: filePath, fullPage: true });
    } catch (err) {
        console.error(`[failureScreenshot] ${subfolder}/${tag}:`, err);
    }
}
