import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.goto("http://localhost:5173/app-store", {
  waitUntil: "networkidle",
  timeout: 30000,
});
await page.waitForTimeout(2000);

await page.screenshot({ path: "/tmp/app-store-final.png", fullPage: true });
console.log("Screenshot saved: /tmp/app-store-final.png");

await browser.close();
