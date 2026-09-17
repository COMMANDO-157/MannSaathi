from backend.models.schemas import EmotionalReading, KnowledgeResult, EscalationTier
from data.knowledge_base import CRISIS_RESOURCES

def determine_tier(reading: EmotionalReading) -> EscalationTier:
    valence = reading.valence_score
    dev = reading.baseline_deviation

    # Combine absolute valence (works from entry #1) with baseline deviation (kicks in after history builds)
    if valence <= -0.6 or dev >= 2.5:
        tier, action = "severe", "Immediately present crisis resources."
    elif valence <= -0.3 or dev >= 1.0:
        tier, action = "moderate", "Nudge toward a real conversation with someone trusted."
    else:
        tier, action = "mild", "Suggest a grounding exercise from knowledge base."

    reasoning = f"Valence {valence:.2f}, baseline deviation {dev:.2f} std devs → '{tier}' tier."
    return EscalationTier(tier=tier, reasoning=reasoning, confidence=min(1.0, abs(valence) + dev / 3), recommended_action=action)

def compose_response(tier: EscalationTier, knowledge: dict | None) -> str:
    if tier.tier == "severe":
        base = CRISIS_RESOURCES["message"] + "\n\n"
        for h in CRISIS_RESOURCES["helplines"]:
            alt = f" / {h['alt_number']}" if "alt_number" in h else ""
            base += f"• {h['name']}: {h['number']}{alt} ({h['availability']}) — {h['note']}\n"
        return base.strip()

    base = f"[{tier.tier.upper()}] {tier.recommended_action}\nReasoning: {tier.reasoning}"
    if knowledge:
        base += f"\nGrounded in: {', '.join(knowledge['sources'])}"
    return base