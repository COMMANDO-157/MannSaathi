# Seed knowledge base: grounding techniques, coping strategies, resources.
# Each entry: (passage_text, source_label)
KNOWLEDGE_BASE = [
    ("Try the 5-4-3-2-1 grounding technique: name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste. This pulls attention back to the present moment.", "Grounding Techniques Guide"),
    ("Box breathing: inhale for 4 seconds, hold for 4 seconds, exhale for 4 seconds, hold for 4 seconds. Repeat for 2-3 minutes to calm the nervous system.", "Breathing Exercises Guide"),
    ("Progressive muscle relaxation involves tensing and then releasing each muscle group in your body, starting from your toes and working upward, to release physical tension linked to stress.", "Relaxation Techniques Guide"),
    ("Journaling about what specifically triggered a difficult emotion, without judgment, can help identify patterns over time and make emotions feel more manageable.", "Self-Reflection Practices"),
    ("A short walk outdoors, even 10 minutes, has been shown to reduce cortisol levels and improve mood through light physical activity and change of environment.", "Movement and Mood Guide"),
    ("Reaching out to one trusted friend or family member, even with a short message, can reduce feelings of isolation during a difficult stretch.", "Social Connection Guide"),
    ("Academic stress before exams is common. Breaking study sessions into 25-minute focused blocks with 5-minute breaks (the Pomodoro technique) can reduce overwhelm.", "Study Stress Management"),
    ("If feelings of sadness or anxiety persist for more than two weeks and interfere with daily functioning, speaking with a counselor or mental health professional is recommended.", "When to Seek Professional Help"),
    ("Sleep disruption often accompanies emotional distress. Keeping a consistent sleep schedule, even during stressful periods, supports emotional regulation.", "Sleep and Emotional Health Guide"),
    ("Gratitude practices, such as writing down three things that went well each day, have been linked to modest but consistent improvements in mood over time.", "Positive Psychology Practices"),
]

CRISIS_RESOURCES = {
    "helplines": [
        {
            "name": "Tele-MANAS (Govt. of India)",
            "number": "14416",
            "alt_number": "1-800-891-4416",
            "availability": "24/7, free, confidential",
            "note": "Available in 20 languages. Connects to a trained counsellor; can refer to a psychiatrist if needed.",
        },
        {
            "name": "iCall (TISS)",
            "number": "9152987821",
            "availability": "Mon-Sat, 8 AM - 10 PM",
            "note": "Free psychosocial support helpline run by the Tata Institute of Social Sciences.",
        },
        {
            "name": "National Emergency Number",
            "number": "112",
            "availability": "24/7",
            "note": "For immediate physical safety emergencies.",
        },
    ],
    "message": (
        "It sounds like things feel really heavy right now. You don't have to go through this alone — "
        "please consider reaching out to Tele-MANAS at 14416, a free, confidential, government-run helpline "
        "available 24/7 in your language. If you're in immediate danger, please call 112."
    ),
}