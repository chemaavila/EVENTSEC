import { test, expect } from "@playwright/test";

const adminEmail = process.env.E2E_ADMIN_EMAIL ?? "admin@example.com";
const adminPassword = process.env.E2E_ADMIN_PASSWORD ?? "Admin123!";

test("login with admin user and sees authenticated UI", async ({ page }) => {
  await page.goto("/login");

  await page.getByLabel("Email").fill(adminEmail);
  await page.getByLabel("Password").fill(adminPassword);
  await page.getByRole("button", { name: /sign in/i }).click();

  await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();

  const cookies = await page.context().cookies();
  const hasAccessToken = cookies.some((cookie) => cookie.name === "access_token");
  expect(hasAccessToken).toBeTruthy();
});
