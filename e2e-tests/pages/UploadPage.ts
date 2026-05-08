import { Page, Locator } from "@playwright/test";

export class UploadPage {
    readonly page: Page;
    readonly fileInput: Locator;
    readonly uploadBtn: Locator;
    readonly resultDiv: Locator;
    readonly scoreText: Locator;

    constructor(page: Page) {
        this.page = page;
        this.fileInput = page.locator('input[type="file"]');
        this.uploadBtn = page.getByRole('button', {name: '评测质量' });
        this.resultDiv = page.locator('#result');
        this.scoreText = page.locator('#result').getByText(/BRISQUE分数/);
    }

    async goto() {
        await this.page.goto('http://localhost:3000');
    }

    async uploadImage(filePath: string) {
        await this.fileInput.setInputFiles(filePath);
        await this.uploadBtn.click();
    }

    async getScore(): Promise<number> {
        const text = await this.scoreText.innerText();
        const match = text.match(/BRISQUE分数：(\d+\.?\d*)/);
        return match ? parseFloat(match[1]) : -1;
    }

    async getQuality(): Promise<string> {
        const text = await this.resultDiv.innerText();
        return text.includes('✅ 合格') ? 'good' : 'bad';
    }
}
