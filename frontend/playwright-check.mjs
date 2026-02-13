import { chromium } from "playwright";

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const errors = [];
  const warnings = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    } else if (msg.type() === "warning") {
      warnings.push(msg.text());
    }
  });

  page.on("pageerror", (err) => {
    errors.push(`PAGE ERROR: ${err.message}`);
  });

  try {
    await page.goto("http://localhost:5173/app-store", {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    await page.waitForTimeout(3000);

    const bodyText = await page.evaluate(() => document.body.innerText);
    const hasAppCards = await page.evaluate(
      () => document.querySelectorAll('[class*="border-light"]').length > 0,
    );

    console.log("=== FRONTEND STATUS ===");
    console.log("Title:", await page.title());
    console.log("Apps found:", bodyText.includes("apps found"));
    console.log("Has app cards:", hasAppCards);
    console.log("\n=== ERRORS (" + errors.length + ") ===");
    errors.forEach((e, i) => console.log(`${i + 1}. ${e}`));
  } catch (err) {
    console.log("NAVIGATION ERROR:", err.message);
  } finally {
    await browser.close();
  }
})();
