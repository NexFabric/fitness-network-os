import { createHmac } from 'node:crypto'
import type { Page } from '@playwright/test'

const OWNER_EMAIL = 'e2e.owner@e2e.local'
const OWNER_TOTP_SECRET =
  process.env.E2E_OWNER_TOTP_SECRET ?? 'JBSWY3DPEHPK3PXP'

function decodeBase32(value: string): Buffer {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
  const bits = value
    .replace(/=+$/u, '')
    .toUpperCase()
    .split('')
    .map((character) => alphabet.indexOf(character).toString(2).padStart(5, '0'))
    .join('')
  const bytes: number[] = []
  for (let index = 0; index + 8 <= bits.length; index += 8) {
    bytes.push(Number.parseInt(bits.slice(index, index + 8), 2))
  }
  return Buffer.from(bytes)
}

export function currentOwnerTotp(now = Date.now()): string {
  const counter = Math.floor(now / 30_000)
  const message = Buffer.alloc(8)
  message.writeBigUInt64BE(BigInt(counter))
  const digest = createHmac('sha1', decodeBase32(OWNER_TOTP_SECRET))
    .update(message)
    .digest()
  const offset = digest[digest.length - 1] & 0x0f
  const binary =
    (((digest[offset] & 0x7f) << 24) |
      ((digest[offset + 1] & 0xff) << 16) |
      ((digest[offset + 2] & 0xff) << 8) |
      (digest[offset + 3] & 0xff)) >>>
    0
  return String(binary % 1_000_000).padStart(6, '0')
}

export async function completeOwnerMfaIfNeeded(page: Page, email: string) {
  if (email !== OWNER_EMAIL) return
  const field = page.locator('#mfa-code')
  await field.waitFor({ state: 'visible', timeout: 10_000 })
  await field.fill(currentOwnerTotp())
  await page.click('button[type="submit"]')
}
