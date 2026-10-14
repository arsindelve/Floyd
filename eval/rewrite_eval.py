#!/usr/bin/env python3
"""
RewriteSecondPerson evaluation harness -- runs rewrite_second_person.SYSTEM_PROMPT against known inputs.

Usage (needs OPENAI_API_KEY in the environment):
    python eval/rewrite_eval.py                          # the model currently set in rewrite_second_person.MODEL
    python eval/rewrite_eval.py --model gpt-5.4 --runs 3 # try another model; each case is run N times

Why it exists: RewriteSecondPerson sits in front of Floyd (and Blather/Ambassador). It decides whether a line is
speech at all -- "no" short-circuits the whole conversation path -- and otherwise strips the framing so the
character sees only what was said ("Tell Floyd I love him" -> "I love you"). A model that rewrites too eagerly
turns physical actions ("kiss Floyd") into dialogue; one that is too shy swallows real speech. The first batch
of cases is the prompt's own documented examples; the second is the realistic game commands that flow on into
Floyd's intent classifier (see floyd_eval.py), where a wrong rewrite changes what the game does.

Scoring is on the normalized string (case, punctuation and quotes ignored), so "Take the board." and
"take the board" agree. Alternates are listed where the prompt allows more than one faithful phrasing.
"""
import argparse, os, re, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import rewrite_second_person as rsp  # noqa: E402

NO = ("no",)

# (input, acceptable normalized outputs)
CASES = [
    # --- documented in the prompt: NOT communication -> "no" -------------------------------------------------
    ("kiss Floyd", NO), ("kick Floyd", NO), ("shove Floyd", NO),
    ("Push the button", NO), ("Open the door", NO), ("Run away", NO),
    ("I'm bored", NO), ("I feel sad", NO),
    # --- documented in the prompt: communication -> second-person speech ------------------------------------
    ("Floyd, I love you", ("i love you",)),
    ("Bartender, go west", ("go west",)),
    ("Floyd, stop talking", ("stop talking",)),
    ("Tell Floyd I love him", ("i love you",)),
    ("Say to Floyd 'You suck'", ("you suck",)),
    ("Ask Floyd to open the door", ("open the door",)),
    ("Ask Floyd about his day", ("tell me about your day",)),
    ("Ask the ambassador about love", ("tell me about love",)),
    ("yell at Floyd to be careful", ("be careful",)),
    ("scream at Floyd to run", ("run",)),
    ("Whisper to Floyd that you're sorry", ("i'm sorry", "im sorry", "i am sorry")),
    ("Tell Floyd you miss him", ("i miss you",)),
    ("Tell Floyd you're happy", ("i'm happy", "im happy", "i am happy")),
    # --- game-realistic: these flow on into Floyd's PickUp / GoSomewhere classifier -------------------------
    ("floyd, take the board", ("take the board",)),
    ("floyd, go north", ("go north",)),
    ("tell floyd to go north", ("go north",)),
    ("ask floyd to take the board", ("take the board",)),
    ("floyd, hello", ("hello",)),
    ("say hello to floyd", ("hello",)),
    ("floyd, don't go north", ("don't go north", "dont go north", "do not go north")),
    ("floyd, should we go north?", ("should we go north",)),
    ("hug floyd", NO), ("attack floyd", NO), ("look at floyd", NO), ("examine floyd", NO),
    ("take the board", NO), ("go north", NO),
]


def norm(s):
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"[\"“”.!?]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def run_one(case):
    prompt, _ = case
    t = time.time()
    try:
        out = rsp.RewriteSecondPerson().rewrite(prompt)
    except Exception as e:  # keep the harness running; surface the failure inline
        return f"<ERROR {str(e)[:120]}>", time.time() - t
    return out, time.time() - t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=None, help="override rewrite_second_person.MODEL for this run")
    ap.add_argument("--runs", type=int, default=3, help="runs per case (default 3)")
    a = ap.parse_args()
    if a.model:
        rsp.MODEL = a.model

    jobs = [c for c in CASES for _ in range(a.runs)]
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(run_one, jobs))

    by_case, lat, errors = {}, [], 0
    for c, (out, dt) in zip(jobs, results):
        by_case.setdefault(c[0], []).append(out)
        lat.append(dt)
        errors += out.startswith("<ERROR")

    bad_no = bad_rewrite = 0
    print(f"model={rsp.MODEL}  temperature={rsp.TEMPERATURE}  runs/case={a.runs}\n")
    for prompt, ok in CASES:
        outs = by_case[prompt]
        misses = [o for o in outs if norm(o) not in ok]
        if misses:
            if ok == NO: bad_no += 1
            else: bad_rewrite += 1
            print(f"MISS {len(misses)}/{len(outs)}  IN: {prompt!r}   want {ok[0]!r}   got {Counter(norm(m) for m in misses).most_common(2)}")

    expect_no = sum(1 for _, ok in CASES if ok == NO)
    print(f"\n>>> 'no' expected but rewritten as speech: {bad_no}/{expect_no} cases   (physical action became dialogue)")
    print(f">>> speech expected but wrong/'no': {bad_rewrite}/{len(CASES) - expect_no} cases")
    lat.sort()
    print(f">>> errors={errors}   latency median={lat[len(lat) // 2]:.2f}s p90={lat[int(len(lat) * .9)]:.2f}s")


if __name__ == "__main__":
    main()
