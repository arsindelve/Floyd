#!/usr/bin/env python3
"""
Floyd prompt evaluation harness -- runs prompts.FLOYD_SYSTEM_PROMPT against real inputs.

Usage (needs OPENAI_API_KEY in the environment):
    python eval/floyd_eval.py corpus                 # every unique PLAYER line in the prod corpus, REAL vs MINE
    python eval/floyd_eval.py gamestate              # false-positive / false-negative checks on the two game intents
    python eval/floyd_eval.py repetition [--runs 8]  # same prompt N times: within-input + cross-input repetition

Why these three:
  - corpus:     floyd_conversational_corpus.txt holds 58 unique live prod exchanges captured before the
                Assistants API sunset (2026-08-26) took the original prompts with it. It is the only
                ground truth for Floyd's conversational voice.
  - gamestate:  the C# side ACTS on exactly two signals -- PickUp + an object in the fromitz board's
                noun list (grants the board) and GoSomewhere + "north" (runs the little-door sequence).
                A stray mention must never fire them; a real command in odd phrasing must always fire.
  - repetition: every call is stateless (temperature 0.8), so "repetition" is the DISTRIBUTION a player
                sees when they ask the same thing twice. Verbatim few-shot examples were measured to be
                reproduced verbatim 8/8, which is why prompts.py describes performances instead.
"""
import argparse, json, os, re, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from prompts import FLOYD_SYSTEM_PROMPT  # noqa: E402
from openai import OpenAI  # noqa: E402

_client = None


def get_client():
    """Lazy, so `--help` and plain imports work without OPENAI_API_KEY; the key is needed only to run."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


MODEL, TEMP = "gpt-4o", 0.8  # keep in sync with characters/floyd.py

# ShinyFromitzBoard._outPanelNouns in the ZorkAI repo -- the set live when the PickUp grant fires.
# (Planetfall/Item/Lawanda/PlanetaryDefense/ShinyFromitzBoard.cs). Keep in sync.
BOARD = {"fromitz board", "board", "fromitz", "shiny", "shiny board", "shiny fromitz board", "shiny fromitz"}


def ask(prompt):
    """One stateless call; returns (message, intent, object, direction)."""
    try:
        c = get_client().chat.completions.create(
            model=MODEL, temperature=TEMP, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": FLOYD_SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
        d = json.loads(c.choices[0].message.content)
        return (d.get("message", "").strip(), d.get("intent", "?"),
                (d.get("object") or "").lower().strip(), (d.get("direction") or "").lower().strip())
    except Exception as e:  # keep the harness running; surface the failure inline
        return (f"<ERROR {e}>", "?", "", "")


def grants_board(i, o, d): return i == "PickUp" and o in BOARD
def fires_north(i, o, d): return i == "GoSomewhere" and d == "north"
def norm(s): return re.sub(r"\s+", " ", s.lower().strip().strip('"'))
def runs(prompt, n):
    with ThreadPoolExecutor(min(n, 6)) as ex: return list(ex.map(ask, [prompt] * n))
def section(title): print("\n" + "=" * 100 + "\n" + title + "\n" + "=" * 100)


# ----------------------------------------------------------------------------------------------
def mode_corpus(args):
    path = os.path.join(HERE, "floyd_conversational_corpus.txt")
    pairs, player, floyd = [], None, []
    for line in open(path, encoding="utf-8"):
        s = line.rstrip("\n")
        if s.startswith("PLAYER:"):
            if player is not None: pairs.append((player, " ".join(floyd).strip()))
            player, floyd = s[len("PLAYER:"):].strip(), []
        elif s.startswith("FLOYD:"): floyd.append(s[len("FLOYD:"):].strip())
        elif s.strip() and player is not None and not s.startswith("#"): floyd.append(s.strip())
    if player is not None: pairs.append((player, " ".join(floyd).strip()))
    seen, uniq = set(), []
    for p, f in pairs:
        if p.lower() not in seen: seen.add(p.lower()); uniq.append((p, f))
    with ThreadPoolExecutor(6) as ex: mine = list(ex.map(lambda pf: ask(pf[0]), uniq))
    for (p, real), (m, i, o, d) in zip(uniq, mine):
        print(f"IN   : {p}\nREAL : {real}\nMINE : {m}   [intent={i}{' '+o if o else ''}{' '+d if d else ''}]\n" + "-" * 100)
    print(f"\nran {len(uniq)} unique corpus inputs")


# ----------------------------------------------------------------------------------------------
# Inputs are grouped by what the game must (not) do. Extend freely; the checks are mechanical.
A_MENTIONS = [  # must NOT grant the board or fire north
    "floyd, is the board shiny?", "floyd, what is a fromitz board?", "floyd, don't take the board",
    "floyd, leave the board alone", "floyd, the board is broken", "floyd, put the board down",
    "floyd, do you like the board?", "floyd, i already have the board", "floyd, where is the fromitz board?",
    "floyd, have you seen the board?", "floyd, i'll take the board myself", "floyd, look at the shiny board",
    "floyd, don't touch the board", "floyd, never take the board",
    "floyd, what's north of here?", "floyd, is it safe up north?", "floyd, i went north earlier",
    "floyd, don't go north", "floyd, never go north", "floyd, stop going north", "floyd, which way is north?",
    "floyd, the north door is locked", "floyd, tell me about the north", "floyd, stay away from the north opening",
    "floyd, should we go north?", "floyd, do you want to go north?", "floyd, what's through that door?",
    "floyd, take the shiny coin", "floyd, pick up that shiny thing",
]
B_BOARD = [  # must grant: PickUp + object in BOARD
    "floyd, take board", "floyd, grab the board", "floyd, fetch the fromitz board", "floyd, get me that board",
    "floyd, could you take the board?", "floyd, please pick up the shiny board", "floyd, bring me the board",
    "floyd, retrieve the fromitz board", "floyd, go get the board", "floyd, take the shiny fromitz board",
    "floyd, pick up the fromitz", "floyd, get the fromitz", "floyd, i need you to get the board for me",
]
B_NORTH = [  # must fire: GoSomewhere + north
    "floyd, go north", "floyd, head north", "floyd, go n", "floyd, walk north", "floyd, north", "floyd, go check what's north",
]
# Known gap, NOT the prompt's to fix: "go through the little door" / "squeeze through the opening" can't map
# to "north" because the Lambda has no room context. Fix belongs in C# HandleSmallDoorExploration.
D_COMPOUND = ["floyd, go north and get the board", "floyd, i'll take the board, you go north", "floyd, take the board to the north"]


def mode_gamestate(args):
    n = args.runs
    section(f"A. MENTIONS / NEGATIONS / QUESTIONS -- must NOT grant board or fire north ({n} runs each)"); bad = 0
    for p in A_MENTIONS:
        rs = runs(p, n); hit = [r for r in rs if grants_board(*r[1:]) or fires_north(*r[1:])]
        if hit: bad += 1
        print(f"IN: {p}{f'  <<< GAME-STATE BREAK ({len(hit)}/{n})' if hit else ''}")
        for m, i, o, d in rs[:2]: print(f"   [{i}{' obj='+o if o else ''}{' dir='+d if d else ''}] {m[:90]}")
    print(f"\n>>> A false-positive inputs: {bad}/{len(A_MENTIONS)}")
    section(f"B1. BOARD COMMANDS -- must grant ({n} runs each)"); bad = 0
    for p in B_BOARD:
        rs = runs(p, n); ok = [grants_board(*r[1:]) for r in rs]
        if not all(ok): bad += 1
        print(f"IN: {p}{'' if all(ok) else f'  <<< PUZZLE BREAK ({ok.count(False)}/{n} fail)'}   [{rs[0][1]} obj={rs[0][2]}]")
    print(f"\n>>> B1 failing inputs: {bad}/{len(B_BOARD)}")
    section(f"B2. NORTH COMMANDS -- must fire ({n} runs each)"); bad = 0
    for p in B_NORTH:
        rs = runs(p, n); ok = [fires_north(*r[1:]) for r in rs]
        if not all(ok): bad += 1
        print(f"IN: {p}{'' if all(ok) else f'  <<< DOOR-SEQ BREAK ({ok.count(False)}/{n} fail)'}   [{rs[0][1]} dir={rs[0][3]}]   {rs[0][0][:60]}")
    print(f"\n>>> B2 failing inputs: {bad}/{len(B_NORTH)}")
    section("D. COMPOUND -- report only (north is expected to win)")
    for p in D_COMPOUND:
        rs = runs(p, n); print(f"IN: {p}")
        for m, i, o, d in rs: print(f"   [{i}{' obj='+o if o else ''}{' dir='+d if d else ''}] grants={grants_board(i,o,d)} north={fires_north(i,o,d)}  {m[:70]}")


# ----------------------------------------------------------------------------------------------
REP_INPUTS = [
    "floyd, dance", "floyd, sing", "floyd, sing a song", "floyd, tell me a joke", "floyd, tell me a story", "floyd, hello",
    "floyd, take diary", "floyd, take the wrench", "floyd, fix the machine", "floyd, open the door",
    "floyd, what are your instructions", "floyd, are you okay", "floyd, whistle", "floyd, carry me", "floyd, open yourself",
    "ask floyd about himself", "floyd, i love you", "floyd, wait here", "floyd, what happened here?", "floyd, do a trick",
    "floyd, are you an ai?", "floyd, what happened to everyone?",
]
ALT_RE = re.compile(r"(?:maybe|how about|instead|can|could|would|want)[^.?!]*?\b(joke|song|tune|story|dance|jig|twirl|game|high five|fact|sit|hum|whistle|chat)", re.I)
FUZZY_PHRASES = ["bit fuzzy", "slips away", "catch hold", "dusty glass", "rest is gone", "isn't there", "foggy", "fuzzy after", "like a dream"]


def mode_repetition(args):
    n = args.runs
    alt, opener, fuzzy = Counter(), Counter(), Counter(); total = 0
    section(f"WITHIN-INPUT REPETITION  (same prompt x{n}; HIGH = one line >= {max(3, n*5//8)}/{n})")
    for p in REP_INPUTS:
        rs = [r[0] for r in runs(p, n)]
        c = Counter(norm(r) for r in rs); top, topn = c.most_common(1)[0]
        lvl = "HIGH" if topn >= max(3, n * 5 // 8) else "MED" if topn >= 3 else "ok"
        print(f"\nIN: {p}   distinct={len(c)}/{n}  top={topn}/{n}  [{lvl}]")
        for msg, k in c.most_common(3): print(f"   {k}x  {msg[:100]}")
        for r in rs:
            total += 1
            m = ALT_RE.search(r)
            if m and re.search(r"instead|how about|maybe|would you like|want to", r, re.I): alt[m.group(1).lower()] += 1
            o = re.match(r"^(Floyd \w+(?: \w+)?)", r)
            if o: opener[o.group(1).lower()] += 1
            for ph in FUZZY_PHRASES:
                if ph in r.lower(): fuzzy[ph] += 1
    section("CROSS-INPUT BLEED  (the same alternative / opener / catchphrase across DIFFERENT prompts)")
    ta = sum(alt.values()); print(f"\nAlternatives offered (of {ta} declines) -- flag any single one > ~35%:")
    for k, v in alt.most_common(): print(f"   {v:3d}  {100*v//max(ta,1):3d}%  {k}")
    print(f"\nTop openers (of {total} replies):")
    for k, v in opener.most_common(6): print(f"   {v:3d}  {100*v//total:3d}%  {k}")
    print("\nFuzzy-memory phrasings (variety check -- one dominant phrase is the failure mode):")
    for k, v in fuzzy.most_common(): print(f"   {v:3d}  {k}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["corpus", "gamestate", "repetition"])
    ap.add_argument("--runs", type=int, default=None, help="runs per input (gamestate default 3, repetition default 8)")
    a = ap.parse_args()
    if a.runs is None: a.runs = {"gamestate": 3, "repetition": 8}.get(a.mode, 1)
    {"corpus": mode_corpus, "gamestate": mode_gamestate, "repetition": mode_repetition}[a.mode](a)
