"""
MISO session brief — runs inside miso-core container.
Queries live DB and prints a structured signal report.
Usage (from EC2): docker exec miso_v5-miso-core-1 python3 /tmp/miso_brief.py
"""
import sqlite3, json, time

c = sqlite3.connect("config/miso_state.db")
c.row_factory = sqlite3.Row
now = time.time()
DAY  = 86400
WEEK = 7 * DAY

print("=== PROVIDER HEALTH (last 7 days) ===")
rows = c.execute("""
  SELECT provider, model,
         COUNT(*) as n,
         SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as fails,
         ROUND(AVG(latency_ms)) as avg_lat,
         ROUND(SUM(COALESCE(cost_usd,0)),4) as total_cost
  FROM routing_heuristics
  WHERE recorded_at > ?
  GROUP BY provider, model
  ORDER BY fails*1.0/MAX(n,1) DESC
""", (now - WEEK,)).fetchall()
for r in rows:
    rate = round(r["fails"] / r["n"] * 100) if r["n"] else 0
    flag = "  <<< HIGH FAIL" if rate >= 30 else ""
    print(f"  {r['provider']}/{r['model']}: {r['n']} calls, {rate}% fail, {r['avg_lat']}ms avg, ${r['total_cost']}{flag}")
if not rows:
    print("  No data.")

print()
print("=== COST ===")
cost24 = c.execute("SELECT ROUND(SUM(COALESCE(cost_usd,0)),4) FROM routing_heuristics WHERE recorded_at > ?", (now - DAY,)).fetchone()[0] or 0
cost7d = c.execute("SELECT ROUND(SUM(COALESCE(cost_usd,0)),4) FROM routing_heuristics WHERE recorded_at > ?", (now - WEEK,)).fetchone()[0] or 0
calls24 = c.execute("SELECT COUNT(*) FROM routing_heuristics WHERE recorded_at > ?", (now - DAY,)).fetchone()[0]
print(f"  Last 24h: ${cost24}  ({calls24} calls)")
print(f"  Last 7d:  ${cost7d}")

print()
print("=== TASK SCORES (last 50 executions) ===")
rows = c.execute("SELECT data FROM flywheel_log WHERE event='execute_done' ORDER BY rowid DESC LIMIT 50").fetchall()
scores = []
for r in rows:
    try:
        d = json.loads(r["data"])
        if d.get("score") is not None:
            scores.append(float(d["score"]))
    except Exception:
        pass
if scores:
    avg = round(sum(scores) / len(scores), 1)
    low = [s for s in scores if s < 75]
    print(f"  Avg: {avg}/100  ({len(scores)} scored, {len(low)} below 75)")
    print(f"  Min: {min(scores)}  Max: {max(scores)}")
else:
    print("  No scored tasks found.")

print()
print("=== ACTIVE GOALS ===")
rows = c.execute(
    "SELECT id, intent, status, goal_type, created_at FROM goals "
    "WHERE status NOT IN ('achieved','failed','archived') ORDER BY created_at DESC LIMIT 10"
).fetchall()
if rows:
    for r in rows:
        age = round((now - (r["created_at"] or now)) / 3600, 1)
        print(f"  [{r['status']}] {r['id'][:12]} | {(r['intent'] or '')[:70]} ({age}h ago)")
else:
    print("  No active goals.")

print()
print("=== ROADMAP ITEMS ===")
for status in ("pending", "running", "done", "failed"):
    n = c.execute("SELECT COUNT(*) FROM roadmap_items WHERE status=?", (status,)).fetchone()[0]
    print(f"  {status}: {n}")
stalled = c.execute(
    "SELECT id, title, started_at, attempt_count FROM roadmap_items "
    "WHERE status='running' AND started_at < ?", (now - 4 * 3600,)
).fetchall()
for r in stalled:
    hrs = round((now - r["started_at"]) / 3600, 1)
    print(f"  STALLED {hrs}h: {(r['title'] or '')[:60]} (attempt #{r['attempt_count']})")

print()
print("=== RECENT FAILURES (last 24h) ===")
rows = c.execute(
    "SELECT data FROM flywheel_log WHERE event='execute_error' AND created_at > ? "
    "ORDER BY created_at DESC LIMIT 5", (now - DAY,)
).fetchall()
if rows:
    for r in rows:
        try:
            d = json.loads(r["data"])
            print(f"  {str(d.get('task_id','?'))[:20]} | {str(d.get('error',''))[:80]}")
        except Exception:
            pass
else:
    print("  None.")

print()
print("=== PRD PIPELINE ===")
prds = c.execute("SELECT COUNT(*) FROM prds WHERE status='active'").fetchone()[0]
assessments = c.execute("SELECT COUNT(*) FROM prd_assessments WHERE assessed_at > ?", (now - WEEK,)).fetchone()[0]
print(f"  Active PRDs: {prds}  |  Assessments (7d): {assessments}")

print()
print("=== FLYWHEEL STATE ===")
for key in ("flywheel_cycle_count", "flywheel_status", "flywheel_last_task"):
    row = c.execute("SELECT value FROM daemon_state WHERE key=?", (key,)).fetchone()
    print(f"  {key}: {row[0] if row else 'unknown'}")

c.close()
