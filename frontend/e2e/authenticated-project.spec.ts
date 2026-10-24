import { expect, test, type Page } from "@playwright/test";

const requiredEnvironmentValue = (name: string): string => {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(`${name} is required for isolated browser E2E tests.`);
  }

  return value;
};

const signIn = async (page: Page): Promise<void> => {
  await page.getByLabel("Email address").fill(
    requiredEnvironmentValue("AI_BAP_E2E_EMAIL"),
  );
  await page.getByLabel("Password").fill(
    requiredEnvironmentValue("AI_BAP_E2E_PASSWORD"),
  );
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("button", { name: /projects/i })).toBeVisible();
};

test("an isolated analyst can create and retrieve a project after reload", async ({
  page,
}) => {
  const projectName = `E2E synthetic project ${Date.now()}`;

  await page.goto("/");
  await signIn(page);

  await page.getByRole("button", { name: /projects/i }).click();
  await page.getByRole("button", { name: /new project/i }).click();
  await page.getByLabel("Project Name").fill(projectName);
  await page.getByLabel("Description", { exact: true }).fill(
    "Synthetic isolated browser E2E project.",
  );
  await page.getByRole("button", { name: "Create Project" }).click();

  await expect(
    page.getByRole("status"),
  ).toContainText("Project created successfully.");
  await expect(page.getByText(projectName, { exact: true })).toBeVisible();

  // The application intentionally keeps the access token in memory; reload
  // requires another normal UI sign-in before checking persisted server data.
  await page.reload();
  await expect(
    page.getByRole("heading", { name: /sign in to your account/i }),
  ).toBeVisible();
  await signIn(page);
  await page.getByRole("button", { name: /projects/i }).click();

  await expect(page.getByText(projectName, { exact: true })).toBeVisible();
});
