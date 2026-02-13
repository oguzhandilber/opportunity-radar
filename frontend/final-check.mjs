import { chromium } from "playwright";

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const errors = [];
  const logs = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
    logs.push(`[${msg.type()}] ${msg.text()}`);
  });

  page.on("pageerror", (err) => {
    errors.push(`PAGE ERROR: ${err.message}`);
  });

  try {
    await page.goto("http://localhost:5173/app-store", {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    await page.waitForTimeout(2000);

    const stats = await page.evaluate(() => {
      const text = document.body.innerText;
      return {
        totalApps: text.match(/TOTAL APPS[\s\S]*?(\d+)/)?.[1],
        appsFound: text.match(/(\d+) apps? found/)?.[1],
        hasError: text.toLowerCase().includes("error"),
        hasWarning: text.toLowerCase().includes("warning"),
      };
    });

    console.log("=== FINAL VERIFICATION ===");
    console.log("Total Apps:", stats.totalApps);
    console.log("Apps Found:", stats.appsFound);
    console.log("Errors:", errors.length);
    console.log("\nErrors list:");
    errors.forEach((e, i) => console.log(`  ${i + 1}. ${e}`));
  } catch (err) {
    console.log("ERROR:", err.message);
  } finally {
    await browser.close();
  }
})();
