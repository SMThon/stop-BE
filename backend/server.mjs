import http from "node:http";
import { createHash, randomBytes, randomUUID } from "node:crypto";
import pg from "pg";
import { z } from "zod";

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine(s => {
  const d = new Date(`${s}T00:00:00Z`);
  return !Number.isNaN(d.valueOf()) && d.toISOString().slice(0, 10) === s;
});
const text = z.string().trim().min(1).max(200);
const purchase = z.object({ platform: text, policyId: text, productName: text, price: z.number().int().min(0).max(2147483647), orderDate: date, receivedDate: date.nullable(), deadline: date.nullable(), status: z.enum(["보관 중", "반품 신청", "환불 완료", "기한 지남"]) }).strict();
const subscription = z.object({ serviceName: text, presetId: text.nullable(), planId: text.nullable(), price: z.number().int().min(0).max(2147483647), cycle: z.enum(["월", "연"]), nextBillingDate: date, trialEndDate: date.nullable(), deadline: date, cancelReminderDate: date, status: z.enum(["이용 중", "해지 예정", "해지 완료"]) }).strict();
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const hash = token => createHash("sha256").update(token).digest("hex");
function send(res, status, data) { res.writeHead(status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" }); res.end(JSON.stringify(data)); }
async function readJson(req) {
  if (!/^application\/json(?:\s*;|$)/i.test(req.headers["content-type"] ?? "")) throw Object.assign(new Error("Content-Type must be application/json"), { status: 415 });
  let body = "";
  for await (const chunk of req) { body += chunk; if (Buffer.byteLength(body) > 16384) throw Object.assign(new Error("Request body too large"), { status: 413 }); }
  try { return JSON.parse(body); } catch { throw Object.assign(new Error("Invalid JSON"), { status: 400 }); }
}
const server = http.createServer(async (req, res) => {
  try {
    const path = new URL(req.url, "http://localhost").pathname;
    if (req.method === "GET" && path === "/health") { await pool.query("SELECT 1"); return send(res, 200, { status: "ok" }); }
    if (req.method === "POST" && path === "/api/users") {
      const token = randomBytes(32).toString("base64url"), id = randomUUID();
      await pool.query("INSERT INTO api_users(id, token_hash) VALUES ($1, $2)", [id, hash(token)]);
      return send(res, 201, { id, token });
    }
    const match = /^\/api\/(purchases|subscriptions)(?:\/([^/]+))?$/.exec(path);
    if (!match) return send(res, 404, { error: "Not found" });
    const token = /^Bearer ([A-Za-z0-9_-]{43})$/.exec(req.headers.authorization ?? "")?.[1];
    if (!token) return send(res, 401, { error: "Bearer token required" });
    const user = await pool.query("SELECT id FROM api_users WHERE token_hash = $1", [hash(token)]);
    if (!user.rowCount) return send(res, 401, { error: "Invalid token" });
    const table = match[1], id = match[2], userId = user.rows[0].id;
    if (id && !uuid.test(id)) return send(res, 400, { error: "Invalid id" });
    if (req.method === "GET") {
      const result = id ? await pool.query(`SELECT id, data FROM ${table} WHERE user_id=$1 AND id=$2`, [userId, id]) : await pool.query(`SELECT id, data FROM ${table} WHERE user_id=$1 ORDER BY created_at DESC LIMIT 200`, [userId]);
      if (id && !result.rowCount) return send(res, 404, { error: "Not found" });
      const records = result.rows.map(row => ({ id: row.id, ...row.data }));
      return send(res, 200, id ? records[0] : records);
    }
    if ((req.method === "POST" && !id) || (req.method === "PUT" && id)) {
      const parsed = (table === "purchases" ? purchase : subscription).safeParse(await readJson(req));
      if (!parsed.success) return send(res, 400, { error: "Invalid input", details: parsed.error.flatten() });
      const recordId = id ?? randomUUID();
      const result = id ? await pool.query(`UPDATE ${table} SET data=$3, updated_at=now() WHERE user_id=$1 AND id=$2 RETURNING id, data`, [userId, id, parsed.data]) : await pool.query(`INSERT INTO ${table}(user_id,id,data) VALUES ($1,$2,$3) RETURNING id,data`, [userId, recordId, parsed.data]);
      if (!result.rowCount) return send(res, 404, { error: "Not found" });
      return send(res, id ? 200 : 201, { id: result.rows[0].id, ...result.rows[0].data });
    }
    if (req.method === "DELETE" && id) {
      const result = await pool.query(`DELETE FROM ${table} WHERE user_id=$1 AND id=$2`, [userId, id]);
      return result.rowCount ? send(res, 200, { deleted: true }) : send(res, 404, { error: "Not found" });
    }
    return send(res, 405, { error: "Method not allowed" });
  } catch (error) { console.error(error); if (!res.headersSent) send(res, error.status ?? 500, { error: error.status ? error.message : "Internal server error" }); else res.destroy(); }
});
server.listen(Number(process.env.PORT || 3000), "0.0.0.0");
async function shutdown() { server.close(async () => { await pool.end(); process.exit(0); }); }
process.on("SIGTERM", shutdown); process.on("SIGINT", shutdown);
