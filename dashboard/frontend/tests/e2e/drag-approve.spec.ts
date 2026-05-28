import { test, expect } from "@playwright/test";

test("drag review→execute on pending Gate 2 resumes pipeline", async ({ page }) => {
  await page.goto("http://localhost:5173/");
  await page.waitForSelector("[data-testid=kanban-board]");
  const card = page.locator("[data-slug=feat-x]");
  await expect(card).toBeVisible();
  const sb = await card.boundingBox();
  const tcol = page.locator("[data-stage=execute]");
  const tb = await tcol.boundingBox();
  await page.mouse.move(sb!.x + 10, sb!.y + 10);
  await page.mouse.down();
  await page.mouse.move(tb!.x + 50, tb!.y + 80, { steps: 10 });
  await page.mouse.up();
  await expect(
    page.locator("[data-stage=execute] [data-slug=feat-x]")
  ).toBeVisible({ timeout: 10000 });
});
