#!/usr/bin/env bash
# miso_brief.sh — Session startup signal brief for MISO hypercritical loop.
# Run at the start of every Claude session to ground analysis in live data.
# Usage: bash miso_brief.sh

KEY="C:/Users/kyle/.ssh/MISO-Ollama-Key.pem"
INSTANCE="i-035db250e922f4168"
PORT=2226

echo "=== MISO SESSION BRIEF =================================="
echo "Generated: $(date -u '+%Y-%m-%d %H:%M UTC')"
echo ""

# ── Tunnel ────────────────────────────────────────────────────────────────────
aws ec2-instance-connect open-tunnel \
  --instance-id "$INSTANCE" --remote-port 22 --local-port "$PORT" &
TUNNEL_PID=$!
sleep 5

SSH="ssh -i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p $PORT ubuntu@localhost"

# ── Ship and run the brief script ─────────────────────────────────────────────
scp -i "$KEY" -o StrictHostKeyChecking=no -P "$PORT" \
  "C:/Users/kyle/miso_brief.py" ubuntu@localhost:/tmp/miso_brief.py

$SSH "sudo docker cp /tmp/miso_brief.py miso_v5-miso-core-1:/tmp/miso_brief.py && \
      sudo docker exec miso_v5-miso-core-1 python3 /tmp/miso_brief.py"

# ── Container error lines ──────────────────────────────────────────────────────
echo ""
echo "=== CONTAINER ERRORS (recent) ==========================="
$SSH "sudo docker logs miso_v5-miso-core-1 --tail 200 2>&1 \
  | grep -iE 'error|exception|traceback|critical|killed|OOM' \
  | grep -v 'StrictHostKey\|level.*info\|status_code.*[24][0-9][0-9]' \
  | tail -15" || true

echo ""
echo "========================================================="
echo "Brief complete. Paste above into your Claude session."
echo "========================================================="

kill $TUNNEL_PID 2>/dev/null || true
