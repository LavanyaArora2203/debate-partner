# test_terminal.py  (place in the project root, next to app.py)
# Run with:  python test_terminal.py
#            python test_terminal.py weak      <- runs the weak-speech calibration test

import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from core.opponent import generate_rebuttal
from core.judge import judge_speech

MOTION = "This house believes that schools should ban smartphones during school hours."
STUDENT_SIDE = "Proposition"
LEVEL = "intermediate"

STRONG_SPEECH = """
Good morning, honourable judges. I am proud to propose that schools should ban smartphones during school hours.

My first argument is that phones destroy concentration. When a student receives a notification, their attention
breaks, and research on attention shows it takes time to refocus. If this happens many times a day, a student
loses a large part of every lesson without even noticing. Therefore, a ban directly protects learning, which is
the main purpose of school.

My second argument is that phones harm social development. At lunch, many students sit together but stare at
their screens instead of talking. Schools are one of the few places where children learn to make friends, handle
disagreements, and speak face to face. If phones are removed, students are forced to build these skills.
Therefore, a ban makes school a healthier community.

Some may say phones are useful for emergencies. But schools already have phone lines at the office, and parents
can call there. This is why the benefits of a ban outweigh the small inconvenience. I proudly propose.
"""

WEAK_SPEECH = """
Phones are bad. Students use them too much. They should not have them in school because it is not good.
Everyone knows this is true. So we should ban phones.
"""


def divider(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def run(speech: str, label: str) -> None:
    divider(f"TEST: {label}")
    print(f"Motion : {MOTION}")
    print(f"Side   : {STUDENT_SIDE}   Level: {LEVEL}")
    print(f"Speech : {len(speech.split())} words")

    # Call 1: opponent
    t0 = time.perf_counter()
    rebuttal = generate_rebuttal(MOTION, STUDENT_SIDE, speech, LEVEL)
    t_opp = time.perf_counter() - t0

    divider("AI OPPONENT REBUTTAL")
    print(rebuttal)
    print(f"\n[{len(rebuttal.split())} words | {t_opp:.1f}s]")

    # Call 2: judge
    t0 = time.perf_counter()
    feedback = judge_speech(MOTION, STUDENT_SIDE, speech, rebuttal)
    t_judge = time.perf_counter() - t0

    divider("JUDGE FEEDBACK")
    s = feedback.scores
    print(f"Scores   Content: {s.content}/10   Style: {s.style}/10   Strategy: {s.strategy}/10")
    print("\nStrengths:")
    for item in feedback.strengths:
        print(f"  + {item}")
    print("\nWeaknesses:")
    for item in feedback.weaknesses:
        print(f"  - {item}")
    print("\nQuotes:")
    for q in feedback.quotes:
        print(f'  "{q.from_student}"\n     -> {q.comment}')
    print(f"\nNext drill: {feedback.next_drill}")
    print(f"\nOverall: {feedback.overall_comment}")
    print(f"\n[judge {t_judge:.1f}s | total {t_opp + t_judge:.1f}s]")

    divider("RAW JSON")
    print(feedback.model_dump_json(indent=2))

    # Quick self-checks
    divider("CHECKS")
    checks = {
        "Scores within 1-10": all(1 <= v <= 10 for v in (s.content, s.style, s.strategy)),
        "2-3 strengths": 2 <= len(feedback.strengths) <= 3,
        "2-3 weaknesses": 2 <= len(feedback.weaknesses) <= 3,
        "At least 1 verified quote kept": len(feedback.quotes) >= 1,
        "Rebuttal not empty": len(rebuttal.split()) > 50,
        "next_drill present": bool(feedback.next_drill.strip()),
    }
    for name, ok in checks.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")


def test_empty_speech() -> None:
    divider("TEST: empty speech should raise ValueError")
    try:
        generate_rebuttal(MOTION, STUDENT_SIDE, "   ", LEVEL)
        print("[FAIL] No error raised")
    except ValueError as e:
        print(f"[PASS] Raised ValueError: {e}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "strong"

    if mode == "weak":
        run(WEAK_SPEECH, "weak speech (should score clearly lower)")
    else:
        run(STRONG_SPEECH, "strong speech")
        test_empty_speech()