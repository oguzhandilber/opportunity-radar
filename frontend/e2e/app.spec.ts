import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("should load dashboard page", async ({ page }) => {
    await page.goto("/");

    // Check title is visible (actual UI shows "MISSION CONTROL")
    await expect(page.locator("h1")).toContainText("MISSION CONTROL");

    // Check sidebar navigation exists - use aside to be more specific
    const sidebar = page.locator("aside");
    await expect(sidebar.getByText("OPPORTUNITY")).toBeVisible();
    await expect(sidebar.getByText("RADAR")).toBeVisible();
    await expect(
      sidebar.getByRole("link", { name: "DASHBOARD" }),
    ).toBeVisible();
    await expect(
      sidebar.getByRole("link", { name: "OPPORTUNITIES" }),
    ).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "SETTINGS" })).toBeVisible();
  });

  test("should show stat cards", async ({ page }) => {
    await page.goto("/");

    // Wait for API call
    await page.waitForTimeout(2000);

    // Check for stat card structure - actual UI uses uppercase
    await expect(page.locator("text=TOTAL OPPORTUNITIES")).toBeVisible();
    await expect(page.locator("text=NEW TARGETS")).toBeVisible();
  });

  test("should have run scan button", async ({ page }) => {
    await page.goto("/");

    // Check for scan button - button has PLAY icon with "RUN SCAN" text
    await expect(page.locator("text=RUN SCAN")).toBeVisible();
  });
});

test.describe("Navigation", () => {
  test("should navigate to opportunities page", async ({ page }) => {
    await page.goto("/");

    // Click opportunities link
    await page.click("text=Opportunities");

    // Check URL changed
    await expect(page).toHaveURL("/opportunities");

    // Check page title - actual UI shows OPPORTUNITIES
    await expect(page.locator("h1")).toContainText("OPPORTUNITIES");
  });

  test("should navigate to settings page", async ({ page }) => {
    await page.goto("/");

    // Click settings link
    await page.click("text=Settings");

    // Check URL changed
    await expect(page).toHaveURL("/settings");

    // Check page title - actual UI shows CONFIGURATION
    await expect(page.locator("h1")).toContainText("CONFIGURATION");
  });
});

test.describe("Opportunities List", () => {
  test("should show empty state when no opportunities", async ({ page }) => {
    await page.goto("/opportunities");

    // Wait for loading to complete
    await page.waitForTimeout(1000);

    // Should show filters button
    await expect(page.locator('button:has-text("Filters")')).toBeVisible();
  });

  test("should toggle filters panel", async ({ page }) => {
    await page.goto("/opportunities");

    // Click filters button
    await page.click('button:has-text("Filters")');

    // Wait for panel animation
    await page.waitForTimeout(500);

    // Check filter options appear - these are labels inside the panel
    await expect(page.getByText("Status", { exact: true })).toBeVisible();
    await expect(page.getByText("Min Score", { exact: true })).toBeVisible();
  });
});

test.describe("Settings Page", () => {
  test("should show settings form", async ({ page }) => {
    await page.goto("/settings");

    // Check for settings structure
    await expect(page.locator("h1")).toContainText("CONFIGURATION");
  });

  test("should show API keys info", async ({ page }) => {
    await page.goto("/settings");

    // Check for API keys section
    await expect(page.getByRole("heading", { name: "API KEYS" })).toBeVisible();
  });
});
