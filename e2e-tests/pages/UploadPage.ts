import path from "path";
import { expect, Locator, Page } from "@playwright/test";
import { captureFullPageFailureShot } from "../helpers/failureScreenshot";

/** 与 frontend/index.html 中静态页入口一致（本地 dev server 端口） */
const BASE_URL = "http://localhost:3000";

/** index.html: <div id="result">，成功/失败/加载态均写在此 */
const RESULT_CONTAINER_SELECTOR = "#result";

/** index.html: <input type="file" id="fileInput" …>，用 id 绑定避免页面上多个 file 时误选 */
const FILE_INPUT_SELECTOR = "#fileInput";

/** index.html: <button …>评测质量</button> */
const UPLOAD_BUTTON_NAME = "评测质量";

/**
 * 成功态由 JS 写入 innerHTML，必含「BRISQUE分数」与「质量判定」两行（见 index.html L41–44）
 * 用正则兼容前后缀（如 🎯），不依赖全角空格变体
 */
const RESULT_SUCCESS_SCORE = /BRISQUE分数/;
const RESULT_SUCCESS_QUALITY = /质量判定/;

/** 从整段结果文案中抠分数（与页面「🎯 BRISQUE分数：0.12」一致） */
const SCORE_FROM_RESULT_REGEX = /BRISQUE分数[：:]\s*([\d.]+)/;

/** 前端在失败时写入的常见提示（用于错误时截图前可读日志） */
const RESULT_ERROR_HINT = /网络请求失败|请求超时|请先选择/;

const UPLOAD_PAGE_FAILURE_SUBFOLDER = "upload-page-failures";

export type UploadImageOptions = {
    /** 点击「评测质量」后，等待成功结果的最长时间（与后端/模型耗时匹配） */
    resultTimeoutMs?: number;
};

export class UploadPage {
    readonly page: Page;
    readonly fileInput: Locator;
    readonly uploadBtn: Locator;
    readonly resultDiv: Locator;
    /** 成功态下含 BRISQUE 分数的那一行（与 index.html 展示一致） */
    readonly scoreText: Locator;

    constructor(page: Page) {
        this.page = page;

        const resultRoot = page.locator(RESULT_CONTAINER_SELECTOR);
        const filePicker = page.locator(FILE_INPUT_SELECTOR);
        const submitBtn = page.getByRole("button", {
            name: UPLOAD_BUTTON_NAME,
        });
        const scoreLine = resultRoot.getByText(RESULT_SUCCESS_SCORE);

        this.resultDiv = resultRoot;
        this.fileInput = filePicker;
        this.uploadBtn = submitBtn;
        this.scoreText = scoreLine;
    }

    private async captureFailureScreenshot(tag: string): Promise<void> {
        await captureFullPageFailureShot(
            this.page,
            UPLOAD_PAGE_FAILURE_SUBFOLDER,
            tag
        );
    }

    /** 打开与 index.html 一致的上传页，并等待关键控件就绪 */
    async goto(): Promise<void> {
        try {
            await this.page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
            await expect(this.fileInput).toBeVisible({ timeout: 15_000 });
            await expect(this.uploadBtn).toBeVisible({ timeout: 15_000 });
        } catch (err) {
            await this.captureFailureScreenshot("goto");
            throw err;
        }
    }

    /**
     * 选图并点击评测；直到 #result 出现与 index.html 成功态一致的文案才返回，
     * 避免仅判断空 div「可见」时把「⏳ 评测中」误判为已出结果。
     */
    async uploadImage(
        filePath: string,
        options?: UploadImageOptions
    ): Promise<void> {
        const resultTimeoutMs = options?.resultTimeoutMs ?? 60_000;

        try {
            await this.fileInput.setInputFiles(filePath);
            await this.uploadBtn.click();

            await expect(this.resultDiv.getByText(RESULT_SUCCESS_SCORE)).toBeVisible({
                timeout: resultTimeoutMs,
            });
            await expect(
                this.resultDiv.getByText(RESULT_SUCCESS_QUALITY)
            ).toBeVisible({ timeout: 15_000 });
        } catch (err) {
            const snippet = await this.resultDiv
                .innerText()
                .catch(() => "(无法读取 #result)");
            if (RESULT_ERROR_HINT.test(snippet)) {
                console.error("[UploadPage] 页面显示错误态:", snippet.slice(0, 500));
            }
            await this.captureFailureScreenshot(
                `uploadImage-${path.basename(filePath)}`
            );
            throw err;
        }
    }

    /** 解析 #result 中的 BRISQUE 分数；与 index.html 成功模板一致 */
    async getScore(): Promise<number> {
        try {
            const text = await this.resultDiv.innerText();
            const match = text.match(SCORE_FROM_RESULT_REGEX);
            return match ? parseFloat(match[1]) : -1;
        } catch (err) {
            await this.captureFailureScreenshot("getScore");
            console.error("[UploadPage] getScore 失败:", err);
            throw err;
        }
    }

    /** 与 index.html 中「质量判定：✅ 合格 / ❌ 不合格」一致 */
    async getQuality(): Promise<string> {
        try {
            const text = await this.resultDiv.innerText();
            return text.includes("✅ 合格") ? "good" : "bad";
        } catch (err) {
            await this.captureFailureScreenshot("getQuality");
            console.error("[UploadPage] getQuality 失败:", err);
            throw err;
        }
    }
}
