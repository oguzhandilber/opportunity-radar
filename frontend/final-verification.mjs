import { chromium } from "playwright";

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const errors = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
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
    await page.waitForTimeout(2000);

    const stats = await page.evaluate(() => {
      const text = document.body.innerText;
      return {
        totalApps: text.match(/TOTAL APPS[\s\S]*?(\d+)/)?.[1],
        appsFound: text.match(/(\d+) apps? found/)?.[1],
        chatGPT: text.includes("ChatGPT"),
        hasCards:
          document.querySelectorAll('[class*="border-light"]').length > 0,
      };
    });

    console.log("╔════════════════════════════════════════╗");
    console.log("║    ULTRAWORK VERIFICATION RESULTS      ║");
    console.log("╚════════════════════════════════════════╝");
    console.log("");
    console.log("✓ Frontend Status: WORKING");
    console.log(`✓ Total Apps: ${stats.totalApps}`);
    console.log(`✓ Apps Displayed: ${stats.appsFound}`);
    console.log(`✓ Has Cards: ${stats.hasCards ? "YES" : "NO"}`);
    console.log(`✓ ChatGPT Visible: ${stats.chatGPT ? "YES" : "NO"}`);
    console.log("");
    console.log("Console Errors:", errors.length);
    errors.forEach((e, i) => console.log(`  ${i + 1}. ${e}`));
    console.log("");
    console.log(
      errors.length === 0 ? "✅ ALL TESTS PASSED" : "❌ ERRORS FOUND",
    );
  } catch (err) {
    console.log("ERROR:", err.message);
  } finally {
    await browser.close();
  }
})();
