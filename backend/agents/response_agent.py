from backend.models.schemas import EmotionalReading, KnowledgeResult, EscalationTier

def determine_tier(reading: EmotionalReading) -> EscalationTier:
    dev = reading.baseline_deviation
    if dev < 1.0:
        tier, action = "mild", "Suggest a grounding exercise from knowledge base."
    elif dev < 2.5:
        tier, action = "moderate", "Nudge toward a real conversation with someone trusted."
    else:
        tier, action = "severe", "Immediately present crisis resources."

    return EscalationTier(
        tier=tier,
        reasoning=f"Baseline deviation of {dev:.2f} std devs triggered '{tier}' tier.",
        confidence=min(1.0, dev / 3.0),
        recommended_action=action,
    )

def compose_response(tier: EscalationTier, knowledge: KnowledgeResult | None) -> str:
    base = f"[{tier.tier.upper()}] {tier.recommended_action}\nReasoning: {tier.reasoning}"
    if knowledge:
        base += f"\nGrounded in: {', '.join(knowledge['sources'])}"
    return base