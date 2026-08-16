import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig, devices } from '@playwright/test';

function loadBackendEnv() {
  const envPath = resolve(__dirname, '../../backend/.env')
  if (!existsSync(envPath)) return
  for (const raw of readFileSync(envPath, 'utf8').split('\n')) {
    const line = raw.trim()
    if (!line || line.startsWith('#')) continue
    const eq = line.indexOf('=')
    if (eq < 1) continue
    const key = line.slice(0, eq)
    let value = line.slice(eq + 1)
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }
    if (process.env[key] === undefined) process.env[key] = value
  }
}

loadBackendEnv()

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
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        RATE_LIMIT_LOGIN_MAX_REQUESTS: '500',
        ENVIRONMENT: 'development',
        ENCRYPTION_KEY:
          process.env.ENCRYPTION_KEY ??
          'MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=',
        E2E_OWNER_TOTP_SECRET:
          process.env.E2E_OWNER_TOTP_SECRET ?? 'JBSWY3DPEHPK3PXP',
        DATABASE_URL:
          process.env.DATABASE_URL ??
          'postgresql+asyncpg://fitness_app:fitness_app_password@localhost:5433/fitness_os',
        MIGRATOR_DATABASE_URL:
          process.env.MIGRATOR_DATABASE_URL ??
          'postgresql+asyncpg://postgres:postgres@localhost:5433/fitness_os',
        REDIS_URL: process.env.REDIS_URL ?? 'redis://localhost:6379/0',
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
