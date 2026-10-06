# core/judge.py
# Assumes:
#   core/llm.py exposes call_llm(system: str, user: str, max_tokens: int = 1000, temperature: float = 0.7) -> str
#   core/schemas.py defines:
#
#   class Scores(BaseModel):
#       content: int = Field(ge=1, le=10)
#       style: int = Field(ge=1, le=10)
#       strategy: int = Field(ge=1, le=10)
#
#   class QuoteComment(BaseModel):
#       from_student: str
#       comment: str
#
#   class Feedback(BaseModel):
#       scores: Scores
#       strengths: list[str]
#       weaknesses: list[str]
#       quotes: list[QuoteComment]
#       next_drill: str
#       overall_comment: str

import json
import re

from pydantic import ValidationError

from core.llm import call_llm
from core.schemas import Feedback

JUDGE_SYSTEM_PROMPT = """You are an experienced, fair debate adjudicator giving feedback to a school student after a practice round.

You will receive a motion, the student's side, the student's speech, and the opponent's rebuttal. Judge ONLY the student's speech. Use the opponent's rebuttal only to check whether the student left strong points unanswered or exposed weaknesses.

SCORING (integers from 1 to 10)

CONTENT: quality of arguments and reasoning.
- Are claims explained with clear logic (assertion, reasoning, evidence, link back to the motion)?
- Are examples relevant and believable?
- Are arguments relevant to the motion?

STYLE: delivery and clarity of expression.
- Is the speech clear, well organised, and easy to follow (signposting, flow)?
- Is the language persuasive and appropriate?
- Note: if the speech is a transcript of audio, do NOT penalise punctuation, spelling, or minor transcription errors.

STRATEGY: how well the speech wins the debate.
- Does it focus on the most important issues of the motion?
- Does it anticipate opposing arguments or respond to them?
- Does it show why its points matter more than the other side's (weighing)?

SCORE ANCHORS
- 3-4: Mostly assertions with little or no explanation; hard to follow or off-topic.
- 5-6: Understandable, with some reasoning, but gaps in explanation, evidence, or structure.
- 7-8: Clear, well-reasoned, and organised, with minor gaps.
- 9-10: Exceptional for this age group. Rare. Do not give 9 or 10 unless the speech is truly outstanding.
Be honest and calibrated. Do not inflate scores to be kind. Most competent student speeches fall between 4 and 7.

FEEDBACK RULES
- Audience: a school student. Be specific, constructive, and encouraging, but never dishonest.
- "strengths": 2 to 3 items. "weaknesses": 2 to 3 items. Each is one concrete sentence tied to the speech.
- "quotes": 2 to 3 items. Each "from_student" must be an EXACT excerpt copied word for word from the student's speech (a short phrase or sentence). "comment" explains what was good or what to improve about that excerpt.
- "next_drill": ONE specific, practical exercise the student can do next (for example, "Rewrite your first argument using Assertion, Reasoning, Evidence, Conclusion in under 60 seconds").
- "overall_comment": 2 to 3 sentences summarising the performance.
- Do not invent things the student did not say.
- If the speech is very short, off-topic, or empty of argument, score low and explain how to improve.

OUTPUT FORMAT
Respond with ONLY a single valid JSON object. No markdown, no code fences, no text before or after. Use exactly this structure:

{"scores": {"content": <integer 1-10>, "style": <integer 1-10>, "strategy": <integer 1-10>}, ...}
"""

RETRY_MESSAGE = (
    "Your previous reply was not valid JSON matching the required structure. "
    "Reply again with ONLY the JSON object, no extra text, no code fences. "
    "Error details: {error}"
)


def _build_user_message(motion: str, student_side: str, speech: str, rebuttal: str) -> str:
    return (
        f"MOTION: {motion}\n"
        f"STUDENT'S SIDE: {student_side}\n\n"
        f"STUDENT'S SPEECH:\n\"\"\"\n{speech.strip()}\n\"\"\"\n\n"
        f"OPPONENT'S REBUTTAL:\n\"\"\"\n{rebuttal.strip()}\n\"\"\"\n\n"
        "Judge the student's speech now and return the JSON."
    )


def _extract_json(raw: str) -> str:
    """Strips code fences and surrounding text, returning the JSON object substring."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model output.")
    return text[start : end + 1]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _keep_only_real_quotes(feedback: Feedback, speech: str) -> Feedback:
    """Removes quotes that do not actually appear in the student's speech."""
    speech_norm = _normalize(speech)
    feedback.quotes = [q for q in feedback.quotes if _normalize(q.from_student) in speech_norm]
    return feedback


def judge_speech(motion: str, student_side: str, speech: str, rebuttal: str) -> Feedback:
    """Judges the student's speech and returns validated structured feedback."""
    if not speech or not speech.strip():
        raise ValueError("Speech is empty.")

    user_message = _build_user_message(motion, student_side, speech, rebuttal)

    raw = call_llm(system=JUDGE_SYSTEM_PROMPT, user=user_message, max_tokens=1200, temperature=0.2,json_mode=True)

    try:
        feedback = Feedback.model_validate_json(_extract_json(raw))
    except (ValueError, ValidationError, json.JSONDecodeError) as first_error:
        # One retry with the error message included
        retry_user = (
            user_message
            + "\n\n"
            + RETRY_MESSAGE.format(error=str(first_error)[:500])
        )
        raw = call_llm(system=JUDGE_SYSTEM_PROMPT, user=retry_user, max_tokens=1200, temperature=0.0,json_mode=True)
        try:
            feedback = Feedback.model_validate_json(_extract_json(raw))
        except (ValueError, ValidationError, json.JSONDecodeError) as second_error:
            raise RuntimeError(
                "The judge could not produce valid feedback. Please try again."
            ) from second_error

    return _keep_only_real_quotes(feedback, speech)