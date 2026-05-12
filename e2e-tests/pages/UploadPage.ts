import path from "path";
import { Locator, Page } from "@playwright/test";
import { captureFullPageFailureShot } from "../helpers/failureScreenshot";

/** 前端入口（与本地静态服务 / dev server 一致） */
const BASE_URL = "http://localhost:3000";

/** 结果区域：成功/错误文案都渲染在此 */
const RESULT_CONTAINER_SELECTOR = "#result";

/** 文件选择：证件照上传控件 */
const FILE_INPUT_SELECTOR = 'input[type="file"]';

/** 主操作按钮的 accessible name */
const UPLOAD_BUTTON_NAME = "评测质量";

/** BRISQUE 分数行文案（允许「BRISQUE分数」与「BRISQUE 分数」两种展示） */
const BRISQUE_SCORE_LINE = /BRISQUE\s*分数/;

/** 分数行内数字捕获：中文冒号或英文冒号 */
const SCORE_VALUE_REGEX = /BRISQUE\s*分数[：:]\s*(\d+\.?\d*)/;

/** 与 helpers 中目录名一致：页面对象层失败截图子目录 */
const UPLOAD_PAGE_FAILURE_SUBFOLDER = "upload-page-failures";

export class UploadPage {
    readonly page: Page;
    readonly fileInput: Locator;
    readonly uploadBtn: Locator;
    readonly resultDiv: Locator;
    readonly scoreText: Locator;

    constructor(page: Page) {
        this.page = page;

        // 先绑定稳定容器，再挂子定位器，避免重复字符串、便于阅读
        const resultRoot = page.locator(RESULT_CONTAINER_SELECTOR);
        const filePicker = page.locator(FILE_INPUT_SELECTOR);
        const submitBtn = page.getByRole("button", {
            name: UPLOAD_BUTTON_NAME,
        });
        const scoreLine = resultRoot.getByText(BRISQUE_SCORE_LINE);

        this.resultDiv = resultRoot;
        this.fileInput = filePicker;
        this.uploadBtn = submitBtn;
        this.scoreText = scoreLine;
    }

    /** 页面对象内操作失败时写全页截图（路径由 helpers 统一约定） */
    private async captureFailureScreenshot(tag: string): Promise<void> {
        await captureFullPageFailureShot(
            this.page,
            UPLOAD_PAGE_FAILURE_SUBFOLDER,
            tag
        );
    }

    /** 打开上传页 */
    async goto(): Promise<void> {
        try {
            await this.page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
        } catch (err) {
            await this.captureFailureScreenshot("goto");
            throw err;
        }
    }

    /** 选择本地图片并点击「评测质量」 */
    async uploadImage(filePath: string): Promise<void> {
        try {
            await this.fileInput.setInputFiles(filePath);
            await this.uploadBtn.click();
        } catch (err) {
            await this.captureFailureScreenshot(
                `uploadImage-${path.basename(filePath)}`
            );
            throw err;
        }
    }

    /** 从结果区解析 BRISQUE 分数；解析失败返回 -1 */
    async getScore(): Promise<number> {
        try {
            const text = await this.scoreText.innerText();
            const match = text.match(SCORE_VALUE_REGEX);
            return match ? parseFloat(match[1]) : -1;
        } catch (err) {
            await this.captureFailureScreenshot("getScore");
            console.error("[UploadPage] getScore 失败:", err);
            throw err;
        }
    }

    /** 根据结果区是否包含「合格」判定 good / bad */
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
