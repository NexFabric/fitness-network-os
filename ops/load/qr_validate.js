import http from "k6/http";
import { check, sleep } from "k6";

// Default 50 VUs. 100/250/500 are rehearsal flags, not CI defaults.
export const options = {
  vus: Number(__ENV.VUS || 50),
  duration: __ENV.DURATION || "30s",
  thresholds: {
    http_req_failed: ["rate<0.05"],
  },
};

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";
const TOKEN = __ENV.AUTH_TOKEN || "";
const TENANT = __ENV.TENANT_ID || "";
const QR = __ENV.QR_TOKEN || "invalid-qr-for-burst";

export default function () {
  const res = http.post(
    `${BASE}/api/v1/access/qr/validate`,
    JSON.stringify({ token: QR }),
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${TOKEN}`,
        "X-Tenant-ID": TENANT,
      },
    },
  );
  check(res, { "status is not 5xx": (r) => r.status < 500 });
  sleep(0.1);
}
