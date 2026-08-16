import http from "k6/http";
import { check, sleep } from "k6";

// Last-seat contention rehearsal. All VUs hit the same session.
export const options = {
  vus: Number(__ENV.VUS || 50),
  iterations: Number(__ENV.ITERATIONS || 50),
  thresholds: {
    http_req_failed: ["rate<0.2"],
  },
};

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";
const TOKEN = __ENV.AUTH_TOKEN || "";
const TENANT = __ENV.TENANT_ID || "";
const SESSION = __ENV.SESSION_ID || "";
const MEMBER = __ENV.MEMBER_ID || "";

export default function () {
  const res = http.post(
    `${BASE}/api/v1/classes/sessions/${SESSION}/book`,
    JSON.stringify({ member_id: MEMBER }),
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${TOKEN}`,
        "X-Tenant-ID": TENANT,
      },
    },
  );
  check(res, {
    "settled": (r) => [200, 201, 409, 422].includes(r.status),
  });
  sleep(0.05);
}
