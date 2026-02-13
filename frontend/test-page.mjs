import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

// Capture console
page.on("console", (msg) => {
  if (msg.type() === "error") {
    console.log("CONSOLE ERROR:", msg.text());
  }
});

page.on("pageerror", (err) => {
  console.log("PAGE ERROR:", err.message);
});

try {
  await page.goto("http://localhost:5173/app-store", {
    waitUntil: "networkidle",
    timeout: 30000,
  });

  // Wait for content to load
  await page.waitForTimeout(3000);

  // Check if apps are in the DOM
  const hasApps = await page.evaluate(() => {
    const cards = document.querySelectorAll('[class*="border-light"]');
    return cards.length > 0;
  });

  console.log("Page loaded successfully");
  console.log("Has app cards:", hasApps);

  // Check title
  const title = await page.title();
  console.log("Page title:", title);

  // Check for specific text
  const pageText = await page.evaluate(() =>
    document.body.innerText.substring(0, 800),
  );
  console.log("Page text preview:");
  console.log(pageText);
} catch (error) {
  console.log("Error:", error.message);
} finally {
  await browser.close();
}
