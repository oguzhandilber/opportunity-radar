import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

page.on("console", (msg) => {
  if (msg.type() === "error") {
    console.log("CONSOLE ERROR:", msg.text());
  }
});

await page.goto("http://localhost:5173/app-store", {
  waitUntil: "networkidle",
  timeout: 30000,
});
await page.waitForTimeout(3000);

const result = await page.evaluate(() => {
  const text = document.body.innerText;
  return {
    hasApps: text.includes("apps found"),
    appCount: text.match(/(\d+) apps? found/)?.[1],
    hasChatGPT: text.includes("ChatGPT"),
    hasTikTok: text.includes("TikTok"),
    hasInstagram: text.includes("Instagram"),
    stats: {
      total: text.match(/TOTAL APPS[\s\S]{0,100}?(\d+)/)?.[1],
      rising: text.match(/RISING[\s\S]{0,50}?(\d+)/)?.[1],
      new: text.match(/NEW[\s\S]{0,50}?(\d+)/)?.[1],
    },
  };
});

console.log("=== Frontend Verification ===");
console.log("Apps found message:", result.hasApps ? "YES" : "NO");
console.log("App count:", result.appCount);
console.log("Has ChatGPT:", result.hasChatGPT ? "YES" : "NO");
console.log("Has TikTok:", result.hasTikTok ? "YES" : "NO");
console.log("Has Instagram:", result.hasInstagram ? "YES" : "NO");
console.log(
  "Stats - Total:",
  result.stats.total,
  "Rising:",
  result.stats.rising,
  "New:",
  result.stats.new,
);

await browser.close();
