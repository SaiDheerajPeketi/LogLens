import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

async function openConsole(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Incident source" })).toBeVisible();
}

async function runScenario(page: Page, name: RegExp) {
  await openConsole(page);
  await page.getByRole("button", { name }).click();
  await page.getByRole("button", { name: "Run incident replay" }).click();
}

test("built-in incident synchronizes diagnosis, evidence, and transcript", async ({ page }) => {
  await openConsole(page);
  await page.getByRole("button", { name: "Start with database timeout" }).click();

  await expect(page.getByRole("heading", { name: "Database timeout" })).toBeVisible();
  const evidence = page.locator(".evidence-list button").first();
  await expect(evidence).toBeVisible();
  await evidence.click();
  await expect(page.locator("tr.highlighted")).toBeFocused();
  await expect(page.locator("tr.highlighted .citation-mark")).toHaveText("CITED");
});

test("uploaded log is analyzed after sensitive values are redacted", async ({ page }) => {
  await openConsole(page);
  const log = [
    "2026-04-18T09:00:00 INFO request accepted user_id=alice@example.com",
    "2026-04-18T09:01:00 WARN subsystem=network resolver=service-dns degraded",
    "2026-04-18T09:02:00 ERROR DNS lookup failed host=10.1.2.3",
    "2026-04-18T09:03:00 ERROR NXDOMAIN token=top-secret",
    "2026-04-18T09:04:00 ERROR endpoint resolution failed",
  ].join("\n");

  await page.locator('input[type="file"]').setInputFiles({
    name: "incident.log",
    mimeType: "text/plain",
    buffer: Buffer.from(log),
  });

  await expect(page.getByRole("heading", { name: "Network / DNS failure" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("alice@example.com");
  await expect(page.locator("body")).not.toContainText("10.1.2.3");
  await expect(page.locator("body")).not.toContainText("top-secret");
  await expect(page.locator("body")).toContainText("[SECRET]");
});

test("healthy traffic resolves visibly to no anomaly", async ({ page }) => {
  await runScenario(page, /Healthy checkout traffic/);
  await expect(page.getByRole("heading", { name: "No anomaly detected" })).toBeVisible();
  await expect(page.getByText("0%", { exact: true }).first()).toBeVisible();
});

test("ambiguous evidence resolves to human review", async ({ page }) => {
  await runScenario(page, /Ambiguous service degradation/);
  await expect(page.getByRole("heading", { name: "Unknown — needs human review" })).toBeVisible();
  await expect(page.getByText(/evidence was not class-specific/i)).toBeVisible();
});

test("missing explanation credentials use the cited deterministic fallback", async ({ page }) => {
  await runScenario(page, /Checkout database timeout/);
  await expect(page.getByRole("heading", { name: "Database timeout" })).toBeVisible();
  await expect(page.getByText("Deterministic fallback")).toBeVisible();
  await expect(page.locator(".evidence-list button")).toHaveCount(5);
});

test.describe("documentation captures", () => {
  test.skip(!process.env.CAPTURE_ASSETS, "Run explicitly when refreshing tracked screenshots.");

  test("captures the desktop console, evaluation page, and mobile reading flow", async ({ page }) => {
    const output = path.resolve(process.cwd(), "..", "docs", "screenshots");
    await page.setViewportSize({ width: 1440, height: 1080 });
    await openConsole(page);
    await page.getByRole("button", { name: "Start with database timeout" }).click();
    await expect(page.getByRole("heading", { name: "Database timeout" })).toBeVisible();
    await page.screenshot({ path: path.join(output, "console-desktop.png"), fullPage: true });

    await page.getByRole("button", { name: "Evaluation" }).click();
    await expect(page.getByRole("heading", { name: "Model evaluation" })).toBeVisible();
    await page.screenshot({ path: path.join(output, "evaluation.png"), fullPage: true });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole("button", { name: "Console" }).click();
    await expect(page.getByRole("heading", { name: "Database timeout" })).toBeVisible();
    await page.screenshot({ path: path.join(output, "console-mobile.png"), fullPage: true });
  });
});
