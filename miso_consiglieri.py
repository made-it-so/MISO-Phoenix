"""
MISO Consiglieri — strategic counsel and meta-governance agent.

The Consiglieri is MISO's advisor layer. Where the Brain Agent answers
factual questions, the Consiglieri advises on strategy, priorities, and
decisions. It operates at the goal level, not the fact level.

Responsibilities:
1. Goal Counsel       — Which goals should be prioritized? Are any in conflict?
2. Decision Audit     — When MISO is about to take an action, evaluate it.
3. Blind Spot Detection — What is MISO not seeing?
4. Live Call Support  — Real-time or manually-triggered counsel during sales calls.
                        Manual: user hits trigger → transcript so far → instant advice.
                        Auto:   keyword detector fires on transcript stream chunks.

The Consiglieri does NOT execute. It advises. Final decisions remain with the
operator (you) or the Goal Kernel.

Live call support latency:
  Local llama3:   15-45s — usable for post-segment review, not real-time
  Frontier (Claude/GPT-4o via ANTHROPIC_API_KEY / OPENAI_API_KEY): 2-5s — real-time viable
"""
import os
import re
from dataclasses import dataclass, field
from miso_swarm_orchestrator import call_model
from miso_goal_kernel import get_active_goals, get_all_goals, print_status

# Frontier escalation for low-latency live call support
def _call_frontier(prompt: str) -> str | None:
    """Try Claude then GPT-4o for fast responses. Returns None if no keys."""
    import requests
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if anthropic_key:
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": "claude-sonnet-4-6", "max_tokens": 500,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"]
        except Exception:
            pass

    if openai_key:
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}",
                         "Content-Type": "application/json"},
                json={"model": "gpt-4o", "max_tokens": 500,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

    return None  # fall back to local model


@dataclass
class Counsel:
    recommendation: str
    reasoning: str
    risks: list[str]
    priority_goal: str | None  # the goal this counsel most serves


class Consiglieri:
    """
    Strategic advisor agent. All advice is grounded in the active goal set.

    Usage:
        c = Consiglieri()
        advice = c.advise_on("Should we add vector search before fixing ingestion?")
        print(advice.recommendation)
    """

    def _goal_summary(self, max_goals: int = 5) -> str:
        goals = get_active_goals()
        if not goals:
            return "No active goals. The system is directionless."
        lines = []
        for g in goals[:max_goals]:
            criteria = "; ".join(g.get("success_criteria", [])[:2])
            pct = g["progress"]["percent_complete"]
            lines.append(
                f"[{g['id']}] P{g['priority']} '{g['title']}' — {pct:.0f}% complete\n"
                f"  Success criteria: {criteria}"
            )
        return "\n".join(lines)

    def advise_on(self, question: str) -> Counsel:
        """
        Provide strategic counsel on a question or decision.
        """
        goal_summary = self._goal_summary()

        prompt = f"""You are the MISO Consiglieri — a strategic advisor operating at the goal level.
You do not execute. You advise. Your counsel must be grounded in the active goals below.

ACTIVE GOALS:
{goal_summary}

QUESTION FOR COUNSEL:
{question}

Provide your response in this exact format:

RECOMMENDATION:
<one clear, direct recommendation>

REASONING:
<2-4 sentences explaining why this serves the active goals>

RISKS:
- <risk 1>
- <risk 2>

PRIORITY GOAL SERVED:
<the goal ID and title this recommendation most advances>

COUNSEL:"""

        response = call_model("reason", prompt, priority=1)

        # Parse structured response
        rec = self._extract_section(response, "RECOMMENDATION")
        reasoning = self._extract_section(response, "REASONING")
        risks_raw = self._extract_section(response, "RISKS")
        priority_goal = self._extract_section(response, "PRIORITY GOAL SERVED")

        risks = [r.lstrip("- •").strip() for r in risks_raw.split("\n") if r.strip()]

        return Counsel(
            recommendation=rec or response,
            reasoning=reasoning,
            risks=risks,
            priority_goal=priority_goal or None,
        )

    def audit_action(self, action: str) -> Counsel:
        """
        Audit a proposed action before it's taken.
        Returns counsel on whether to proceed, modify, or abort.
        """
        goal_summary = self._goal_summary()

        prompt = f"""You are the MISO Consiglieri. An action is about to be taken. Audit it.

ACTIVE GOALS:
{goal_summary}

PROPOSED ACTION:
{action}

Evaluate this action strictly against the active goals.
- Does it advance an active goal?
- Does it contradict or undermine any goal?
- Are there unintended side effects?

Respond in this format:

RECOMMENDATION:
PROCEED | MODIFY | ABORT

REASONING:
<your reasoning>

RISKS:
- <risk>

PRIORITY GOAL SERVED:
<goal id and title, or "NONE - this action does not serve any active goal">

COUNSEL:"""

        response = call_model("reason", prompt, priority=1)

        rec = self._extract_section(response, "RECOMMENDATION")
        reasoning = self._extract_section(response, "REASONING")
        risks_raw = self._extract_section(response, "RISKS")
        priority_goal = self._extract_section(response, "PRIORITY GOAL SERVED")
        risks = [r.lstrip("- •").strip() for r in risks_raw.split("\n") if r.strip()]

        return Counsel(
            recommendation=rec or "PROCEED",
            reasoning=reasoning,
            risks=risks,
            priority_goal=priority_goal or None,
        )

    def detect_blind_spots(self) -> str:
        """
        Identify what the active goals are missing — risks, dependencies,
        contradictions, or gaps that could cause goal failure.
        """
        all_goals = get_all_goals()
        if not all_goals:
            return "No goals defined. The most critical blind spot is the absence of a mission."

        goals_json = "\n".join(
            f"[{g['id']}] {g['title']} ({g['status']}) — "
            f"criteria: {'; '.join(g.get('success_criteria', []))}"
            for g in all_goals
        )

        prompt = f"""You are the MISO Consiglieri. Analyze these goals for blind spots.

GOALS:
{goals_json}

Identify:
1. Goals with success criteria that are unmeasurable or vague
2. Goals that contradict or block each other
3. Missing prerequisites (what must be true before a goal can be achieved?)
4. Goals that are missing entirely (what is the system NOT working toward that it should be?)

Be specific and ruthless. Do not validate. Identify real gaps.

BLIND SPOT ANALYSIS:"""

        return call_model("reason", prompt, priority=2)

    # ── Live Call Support ─────────────────────────────────────────────────────

    def live_counsel(
        self,
        transcript: str,
        question: str | None = None,
        call_context: dict | None = None,
    ) -> str:
        """
        Tactical counsel during a sales call — manually triggered or automatic.

        Uses frontier models (Claude/GPT-4o) for ~3s latency when API keys are
        present in the environment. Falls back to local model (~30s).

        Args:
            transcript:    Full or partial call transcript accumulated so far.
            question:      Optional specific question. If None, Consiglieri
                           surfaces the 3 most important things to act on.
            call_context:  Optional dict: prospect_name, company, deal_size,
                           stage, our_goals.
        """
        active_goals = get_active_goals()
        goal_str = "\n".join(f"- {g['title']}" for g in active_goals[:3]) \
            or "No active goals defined."

        context_str = ""
        if call_context:
            context_str = "\nCALL CONTEXT:\n" + "\n".join(
                f"  {k}: {v}" for k, v in call_context.items()
            )

        question_str = f"\nSPECIFIC QUESTION: {question}" if question else \
            "\nNo specific question — surface the 3 most important things to act on right now."

        prompt = f"""You are MISO's Consiglieri providing LIVE CALL SUPPORT.
Be brief. Be tactical. No fluff. The operator is on a call RIGHT NOW.

ACTIVE GOALS:
{goal_str}
{context_str}

TRANSCRIPT SO FAR:
{transcript[-3000:]}
{question_str}

Respond with ONLY 3-5 bullet points. Each: one sentence, immediately actionable.
Start each bullet with: ▸
Special flags (add if detected):
  🚀 TRAVEL TRIGGER DETECTED: <city>, <date>  — if onsite meeting was scheduled
  💰 BUYING SIGNAL: <exact quote>              — if strong purchase intent
  ⚠️ OBJECTION: <quote> → <one-line response>  — if objection raised

LIVE BRIEF:"""

        response = _call_frontier(prompt) or call_model("reason", prompt, priority=1)
        return response.strip()

    def watch_for_triggers(self, transcript_chunk: str) -> dict:
        """
        Lightweight automatic scanner for a new transcript chunk (~30s of audio).
        Regex-first (zero LLM cost). Only calls LLM if a pattern fires.

        Returns dict of detected triggers, empty if nothing notable.
        Trigger keys: "travel", "buying", "objection", "structured" (LLM extraction).
        """
        chunk_lower = transcript_chunk.lower()
        triggers = {}

        travel_patterns = [
            r"come (to|visit|see) (us|our office|our hq|the office)",
            r"(meet|meeting|visit) (onsite|in person|in chicago|in new york|in sf|in dallas|in boston|in seattle|in miami|in la|in los angeles|in denver|in atlanta)",
            r"fly (you|your team) (out|in|to)",
            r"(onsite|on.?site) (meeting|visit|demo|presentation)",
            r"we('d| would) like (you|your team) to come",
            r"(host|have) you (here|at our)",
        ]
        buying_patterns = [
            r"(ready to|want to|looking to) (move forward|sign|purchase|buy|get started|proceed)",
            r"(what('s| is) (the|your)) (price|cost|investment|pricing)",
            r"send (me|us) (a |the )?(proposal|contract|agreement|sow|statement of work)",
            r"(budget|funding) (is|has been) (approved|allocated|confirmed)",
        ]
        objection_patterns = [
            r"(too expensive|not in (our )?budget|can't afford|cost is (too )?(high|much))",
            r"(not (the right|a good) time|bad timing|come back (in|next))",
            r"need to (talk to|check with|get approval from)",
        ]

        for p in travel_patterns:
            if re.search(p, chunk_lower):
                triggers["travel"] = True
                break
        for p in buying_patterns:
            if re.search(p, chunk_lower):
                triggers["buying"] = True
                break
        for p in objection_patterns:
            if re.search(p, chunk_lower):
                triggers["objection"] = True
                break

        if triggers:
            extract_prompt = f"""Extract structured data from this call chunk. Return only JSON.

CHUNK: {transcript_chunk[-1000:]}

{{"travel_trigger": {{"detected": true/false, "city": "...", "date": "...", "confidence": "high/medium/low"}}, "buying_signal": {{"detected": true/false, "quote": "..."}}, "objection": {{"detected": true/false, "type": "price/timing/authority/other", "quote": "..."}}}}

JSON:"""
            raw = _call_frontier(extract_prompt) or call_model("fast", extract_prompt)
            try:
                json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                if json_match:
                    import json as _json
                    triggers["structured"] = _json.loads(json_match.group())
            except Exception:
                pass

        return triggers

    def _extract_section(self, text: str, header: str) -> str:
        """Extract content after a header, stopping at the next header."""
        lines = text.split("\n")
        capture = False
        result = []
        for line in lines:
            if line.strip().upper().startswith(header.upper() + ":") or line.strip().upper() == header.upper() + ":":
                capture = True
                inline = line.split(":", 1)[-1].strip()
                if inline:
                    result.append(inline)
                continue
            if capture:
                if line.strip().endswith(":") and line.strip() == line.strip().upper() and len(line.strip()) > 3:
                    break
                result.append(line)
        return "\n".join(result).strip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    c = Consiglieri()

    print("\n[CONSIGLIERI] Strategic Counsel Layer — Online")
    print_status()

    print("\nOptions:")
    print("  1. Ask for counsel on a question")
    print("  2. Audit a proposed action")
    print("  3. Detect blind spots in current goals")
    print("  4. Live call support (paste transcript)")
    print("  q. Quit")

    while True:
        try:
            choice = input("\n[CONSIGLIERI] > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "q":
            break
        elif choice == "1":
            q = input("Question: ").strip()
            if q:
                result = c.advise_on(q)
                print(f"\n[RECOMMENDATION]\n{result.recommendation}")
                print(f"\n[REASONING]\n{result.reasoning}")
                if result.risks:
                    print(f"\n[RISKS]\n" + "\n".join(f"  • {r}" for r in result.risks))
                if result.priority_goal:
                    print(f"\n[SERVES GOAL]\n  {result.priority_goal}")
        elif choice == "2":
            a = input("Proposed action: ").strip()
            if a:
                result = c.audit_action(a)
                print(f"\n[VERDICT] {result.recommendation}")
                print(f"\n[REASONING]\n{result.reasoning}")
                if result.risks:
                    print(f"\n[RISKS]\n" + "\n".join(f"  • {r}" for r in result.risks))
        elif choice == "3":
            print("\n[BLIND SPOT ANALYSIS]")
            print(c.detect_blind_spots())
        elif choice == "4":
            print("Paste transcript (enter END on a blank line when done):")
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                except EOFError:
                    break
            transcript = "\n".join(lines)
            if transcript.strip():
                q = input("Specific question? (leave blank for auto-brief): ").strip() or None
                print("\n[LIVE BRIEF]")
                print(c.live_counsel(transcript, question=q))
