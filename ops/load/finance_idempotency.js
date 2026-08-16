import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: Number(__ENV.VUS || 20),
  iterations: Number(__ENV.ITERATIONS || 40),
};

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";
const TOKEN = __ENV.AUTH_TOKEN || "";
const TENANT = __ENV.TENANT_ID || "";
const ACCOUNT = __ENV.BILLING_ACCOUNT_ID || "";
const KEY = __ENV.IDEMPOTENCY_KEY || "load-pay-shared-key";

export default function () {
  const res = http.post(
    `${BASE}/api/v1/finance/payments`,
    JSON.stringify({
      billing_account_id: ACCOUNT,
      amount_minor: 100,
      method: "CASH",
      allocations: [],
    }),
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${TOKEN}`,
        "X-Tenant-ID": TENANT,
        "Idempotency-Key": KEY,
      },
    },
  );
  check(res, { "not 5xx": (r) => r.status < 500 });
  sleep(0.05);
}
