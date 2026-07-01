"""
MISO Consiglieri — strategic counsel and meta-governance agent.

The Consiglieri is MISO's advisor layer. Where the Brain Agent answers
factual questions, the Consiglieri advises on strategy, priorities, and
decisions. It operates at the goal level, not the fact level.

Responsibilities:
1. Goal Counsel     — Which goals should be prioritized? Are any in conflict?
2. Decision Audit   — When MISO is about to take an action, the Consiglieri
                      evaluates whether it serves active goals.
3. Blind Spot Detection — What is MISO not seeing? What risks are unaddressed?
4. Proposal Critique — Given a plan, identify the weakest assumptions.

The Consiglieri does NOT execute. It advises. Final decisions remain with the
operator (you) or the Goal Kernel.
"""
from dataclasses import dataclass
from miso_swarm_orchestrator import call_model
from miso_goal_kernel import get_active_goals, get_all_goals, print_status


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
                # Stop at next section header (ALL CAPS line ending with colon)
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
