import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command:
        'cd ../../backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/ready',
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        RATE_LIMIT_LOGIN_MAX_REQUESTS: '500',
      },
    },
    {
      command: 'npm --prefix ../admin-web run dev -- --port 5173',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
    },
    {
      command: 'npm --prefix ../scanner-pwa run dev -- --port 5174',
      url: 'http://localhost:5174',
      reuseExistingServer: true,
    },
  ],
});
