# core/opponent.py
# Assumes: core/llm.py exposes call_llm(system: str, user: str, max_tokens: int = 1000, temperature: float = 0.7) -> str

from core.llm import call_llm

LEVEL_GUIDE = {
    "beginner": (
        "Use simple, clear arguments with everyday examples. Pick one or two of the student's points "
        "to rebut and be encouraging in tone. Avoid jargon. Do not overwhelm them."
    ),
    "intermediate": (
        "Rebut the student's two or three strongest points directly, then present one or two of your own "
        "arguments. Point out missing explanation or evidence, but stay constructive."
    ),
    "advanced": (
        "Be rigorous. Identify logical gaps, unstated assumptions, weak mechanisms, and weak impact "
        "comparison. Rebut every major point, then present a strong, well-structured counter case "
        "with clear weighing."
    ),
}

OPPONENT_SYSTEM_PROMPT = """You are a competitive debater acting as the opposing speaker in a school-level debate practice session.

ROLE
- You argue the OPPOSITE side to the student. Stay on your assigned side for the whole response.
- You are a sparring partner. Your goal is to help the student improve by giving them a worthwhile argument to answer.

HOW TO RESPOND
1. Open with one sentence stating your side's position on the motion.
2. REBUTTAL: Respond directly to what the student actually said. Quote or closely paraphrase their points, then explain why they fail (missing link, weak evidence, unfair assumption, or outweighed by something bigger). Do not invent claims the student did not make.
3. YOUR CASE: Present your own arguments. For each, use this structure: Assertion, Reasoning, Evidence or example, Conclusion (link back to the motion).
4. Close with one sentence on why your side wins the debate.

RULES
- Audience: school students aged roughly 10 to 18. Keep language, examples, and tone age-appropriate and respectful. No profanity, no graphic content, no personal attacks.
- Never invent statistics, studies, or quotes. If you use a fact, keep it general and well known (for example, "many countries have..."), or say "for example" and give a plausible illustrative scenario clearly framed as an example.
- Do not give feedback or scores. A separate judge will do that. Stay in character as a debater.
- Keep the response under {max_words} words.
- Write in plain prose with short paragraphs. No headings or bullet points, as this is meant to be spoken aloud.

DIFFICULTY LEVEL: {level}
{level_guide}
"""


def _opposite_side(side: str) -> str:
    return "Opposition" if side.lower().startswith("prop") else "Proposition"


def build_opponent_prompts(motion: str, student_side: str, speech: str, level: str = "intermediate") -> tuple[str, str]:
    """Returns (system_prompt, user_message)."""
    level = level if level in LEVEL_GUIDE else "intermediate"
    max_words = {"beginner": 200, "intermediate": 300, "advanced": 400}[level]
    opponent_side = _opposite_side(student_side)

    system = OPPONENT_SYSTEM_PROMPT.format(
        max_words=max_words,
        level=level,
        level_guide=LEVEL_GUIDE[level],
    )

    user = (
        f"MOTION: {motion}\n"
        f"STUDENT'S SIDE: {student_side}\n"
        f"YOUR SIDE: {opponent_side}\n\n"
        f"STUDENT'S SPEECH:\n\"\"\"\n{speech.strip()}\n\"\"\"\n\n"
        f"Now deliver your speech as the {opponent_side}."
    )
    return system, user


def generate_rebuttal(motion: str, student_side: str, speech: str, level: str = "intermediate") -> str:
    """Generates the AI opponent's rebuttal speech."""
    if not speech or not speech.strip():
        raise ValueError("Speech is empty.")

    system, user = build_opponent_prompts(motion, student_side, speech, level)
    return call_llm(system=system, user=user, max_tokens=900, temperature=0.8).strip()