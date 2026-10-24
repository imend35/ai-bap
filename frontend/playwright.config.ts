import { defineConfig } from "@playwright/test";

const requiredEnvironmentValue = (name: string): string => {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(`${name} is required for isolated browser E2E tests.`);
  }

  return value;
};

const e2eBaseUrl = requiredEnvironmentValue("AI_BAP_E2E_BASE_URL");
const parsedBaseUrl = new URL(e2eBaseUrl);
const loopbackHosts = new Set(["127.0.0.1", "localhost", "::1"]);

if (parsedBaseUrl.protocol !== "http:" || !loopbackHosts.has(parsedBaseUrl.hostname)) {
  throw new Error(
    "AI_BAP_E2E_BASE_URL must use http and a loopback-only host.",
  );
}

if (process.env.AI_BAP_E2E_ISOLATED !== "true") {
  throw new Error(
    "AI_BAP_E2E_ISOLATED must be literal true before browser E2E tests run.",
  );
}

const browserExecutablePath = process.env.AI_BAP_E2E_BROWSER_EXECUTABLE_PATH?.trim();

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: parsedBaseUrl.toString(),
    browserName: "chromium",
    channel: browserExecutablePath ? undefined : "chrome",
    launchOptions: browserExecutablePath
      ? { executablePath: browserExecutablePath }
      : undefined,
    screenshot: "off",
    trace: "off",
    video: "off",
  },
});
