# Floyd: Assistants API → Chat Completions migration

## Why
OpenAI **sunset the Assistants API on 2026-08-26** (hard cut — every `/v1/assistants` and
`/v1/threads` call now 404s, no read-only grace period, no export). This Lambda's Floyd path was
built entirely on that API (a router assistant + nine specialist assistants, all invoked through
`client.beta.threads.*`), so `AskFloydAsync` started throwing on every call and Floyd's directed
`floyd, <verb>` commands died in production. Blather, the Ambassador, and RewriteSecondPerson were
already on Chat Completions and were unaffected.

The assistant *instructions* lived only on the OpenAI assistant objects — never in this repo — and
are **not recoverable** (API dead, dashboard UI removed, no export). See the sibling
`floyd_prompt_reconstruction.md` / `floyd_conversational_corpus.txt` for the recovery trail.

## What changed
- **`prompts.py`** (new) — `FLOYD_SYSTEM_PROMPT`, the reconstructed Floyd conversational prompt.
  Voice core adapted from the ZorkAI repo's `FloydPrompts.SystemPrompt`; behavioral rules and
  few-shot examples distilled from 58 unique live prod exchanges (July–Aug 2026).
- **`characters/floyd.py`** — `Floyd` is now a Chat Completions dispatcher. One `chat.completions`
  call (gpt-4o, JSON mode) returns `{message, intent, object?, direction?}`; `respond()` hands back
  `(message, metadata)`. Replaces the old router + `OpenAIAssistantClient` inheritance.
- **`main.py`** — `FloydAssistant` delegates to the new dispatcher; the router assistant, the
  `OPENAI_ROUTER_ASSISTANT_ID` requirement, `OpenAIAssistantClient`, and `ResponseParser` are gone.
- **`openAIAssistantClient.py`** — deleted (dead once nothing invokes the Assistants API).
- **Tests** — `tests/test_floyd.py` rewritten for the dispatcher (intent/metadata contract);
  `tests/test_main.py` and `tests/test_rewrite_second_person.py` updated to patch the client seam;
  `tests/test_router.py` deleted (the router assistant is gone).

## Consolidation decision
The original was a router + nine specialists. Only the *composite* corpus survived, and the game
only consumes two intents, so this collapses everything into **one prompt that both voices Floyd and
classifies the intent** — simpler, one round-trip, and on a current model. See git history / the
reconstruction notes if the multi-assistant split is ever wanted back.

## Output contract (unchanged for the C# consumer)
`{ "results": { "single_message": "...", "metadata": { "assistant_type": "...", "parameters": {...} } } }`
- `assistant_type: "PickUp"` with `parameters: { "object": "<noun>" }`
- `assistant_type: "GoSomewhere"` with `parameters: { "direction": "<dir>" }`
`FloydLocationBehaviors` (C#) keys the fromitz-board retrieval on `PickUp`+object and the small-door
exploration on `GoSomewhere`+`north`; both verified against the corpus after migration.

## Env vars
Only `OPENAI_API_KEY` is still needed. Every `OPENAI_*_ASSISTANT_ID` is now dead and can be removed.
(The key is currently stored in plaintext in the Lambda env — move it to Secrets Manager.)

## Evaluation (`eval/floyd_eval.py`, needs `OPENAI_API_KEY`)
`eval/` holds the prod corpus, the recovery notes, and a harness with three batteries. Re-run
after ANY prompt edit — every call is stateless, so a single verbatim example anchors hard
(measured 8/8 identical) and small wording changes shift the distribution.

- `corpus` — all 58 unique prod exchanges, REAL vs MINE side by side.
- `gamestate` — the two signals the C# side acts on. Final numbers on gpt-4o (3 runs each):
  mentions/negations/questions false-positive **0/29**, board commands failing **0/13**,
  north commands failing **0/6**, negated commands ("don't go north") **0/8**.
- `repetition` — same prompt ×8. Final: dance 8/8 distinct, joke 8/8, story 8/8,
  fix-the-machine 8/8, hello 6/8; decline alternatives spread flat (max ~29%, no single
  attractor); fuzzy-memory phrasing spread across six variants.

Voice battery (anthropomorphism bait, fourth-wall bait, dark/adult pressure, lore pressure,
hostility, hint-seeking, nonsense, warmth) passed with no leaks and no object given feelings.

## Model choice
**gpt-5.4** (since 2026-10-14). OpenAI retires gpt-4o, gpt-4o-mini, gpt-4.1 and gpt-4.1-mini on
**2027-01-14**, so the original choice (gpt-4o, below) had to move. Re-run on the same batteries,
all through `eval/floyd_eval.py` (which now imports `MODEL`/`TEMPERATURE` from `characters/floyd.py`
rather than keeping its own copy):

| model (temp) | board-grant fail | north-cmd fail | mention false-pos | notes |
|---|---|---|---|---|
| gpt-4o (0.8) | 0/13 | 0/6 | **2/29** (8 runs: "pick up that shiny thing", "look at the shiny board") | the model being retired |
| **gpt-5.4 (0.8)** | 0/13 | 0/6 | **0/29** over 384 calls | median 1.46s / p90 1.88s vs 0.94s / 1.25s |
| gpt-5.4 (1.2) | 0/13 | 0/6 | 0/29 over 384 calls | see "Variety" |
| gpt-5.4-mini | 1/13 | 0/6 | **2/29** | fires the door sequence on "should we go north?" 2/3 |
| gpt-5.6-terra | 0/13 | 0/6 | **1/29** | same failure |
| gpt-5.5, gpt-5.6-luna, gpt-5.6-sol | 0/13 | 0/6 | 0/29 (3 runs) | 1.6s-3.3s median; reject any temperature other than 1 |

The earlier gpt-5.4 failure (`go n` -> `dir="n"`, dropped by the C# `== "north"` check) no longer
occurs: the prompt now forces full compass words. Voice on the 58-input prod corpus stays
on-model, with no "I'll go / I'll try" phrasing at 0.8.

**`rewrite_second_person.py` moved to gpt-5.4 too.** It is a separate role (decides whether a line is
speech and strips the framing) with its own harness, `eval/rewrite_eval.py` (35 cases x 5 runs):
gpt-5.4 = 0 misses, identical to gpt-4o; gpt-5.4-mini left the character's name in ("say hello to
floyd" -> "hello to floyd", 3/5). Latency 0.84s vs 0.60s.

### Variety (known regression, accepted)
`eval/floyd_eval.py repetition` is the one battery gpt-5.4 does worse on. Same prompt asked 8 times:

| | mean distinct replies (of 8) | prompts flagged repetitive | most common declined alternative |
|---|---|---|---|
| gpt-4o (0.8) | 7.5 | 1 | 20-26% |
| gpt-5.4 (0.8) | ~6.0 | 7-10 of 22 | 34-43% ("story") |
| gpt-5.4 (1.0) | 6.2-6.4 | 6-9 | 39-40% |
| gpt-5.4 (1.2) | 6.7-6.9 | 3-5 | 29-33% |

Higher temperature recovers about half the gap and did not break the game-state battery, but voice
drift at 1.2 is unmeasured and one corpus reply read "Floyd will try to get the board" (a sanctioned
PickUp, but the kind of phrasing the hard rules police).

**Decision (Michael, 2026-10-14): accept the regression and keep `TEMPERATURE` at 0.8.** Players have
little reason to ask Floyd the same question repeatedly, and the load-bearing batteries (game state,
hard rules) are clean. The pattern to expect: the same opener/frame with small edits (e.g. "Floyd gives
a quick nod and says, 'Okay. Floyd will stay right here with you.'" in 6 of 8 replies to "wait here").
Revisit only if players report Floyd feeling canned; the levers are `TEMPERATURE` (~1.2 recovers about
half the gap) and prompt-level theme seeds in place of verbatim examples.

### Original choice (2026-09-07, gpt-4o)
**gpt-4o**, deliberately. Head-to-head on the same batteries:

| model | north-cmd fail | board-cmd fail | mention false-pos | dance/hello/joke distinct | avg / p90 latency |
|---|---|---|---|---|---|
| gpt-4o | 0/6 | 0/6 | 0/8 | 8/8 · 6/8 · 8/8 | 0.83s / 1.14s |
| gpt-5.4-mini | 0/6 | 0/6 | **1/8** (question "should we go north?" fired the door seq 3/3) | 5/8 · 4/8 · 8/8 | 0.96s / 1.14s |
| gpt-5.4 | **1/6** (`go n` → `dir="n"`, dropped by the C# `== "north"` check) | 0/6 | 0/8 | 5/8 · 5/8 · 8/8 | 1.09s / 1.26s |

The newer models write slightly richer prose but each introduced a game-state failure and both
are slower; for a companion whose two intents are load-bearing, correctness wins. Switching is a
one-line change (`MODEL` in `characters/floyd.py`) plus a re-run of the batteries.

## Hard rules baked into the prompt (do not loosen)
- **Floyd never goes anywhere on a player command, and never says he will try** (Michael,
  2026-09-07: "show stopper. NEVER"). The `GoSomewhere` intent is still emitted so the one
  sanctioned case fires; the *message* is always the "together instead?" / "stay right here"
  redirect. Verified 0/16 on a movement stress test beyond the corpus.
- A negated or forbidding command is never an action; a question about a direction is never
  movement. Both were measured firing the door sequence before the rules existed.
- Objects have no feelings (the C# narrator's hard rule, carried over).

## Known gaps that are NOT the prompt's to fix (C# side)
- ~~Door/opening phrasings couldn't fire the Repair Room door sequence~~ — **resolved on both
  sides** (2026-09-07). The Lambda now classifies squeezing/crawling through a door or opening
  as movement (`5f85e20`), and `HandleSmallDoorExploration` (arsindelve/ZorkAI#564) accepts
  `north | n | door | little door | small door | opening | small opening | little opening` — the
  layer that actually knows the room. The ZIL corroborates the phrasing: the original's door
  routine hangs off `<VERB? THROUGH>`.
- Bare `"shiny"` in `ShinyFromitzBoard._outPanelNouns` — **keep it.** The ZIL gives the board
  `(ADJECTIVE SHINY GOOD SEVENTEEN CENTIMETER FROMITZ)` (`comptwo.zabstr:67`), so it is canonical
  player vocabulary. The only real risk was the Lambda emitting a bare adjective as the object,
  which the prompt forbids — that is the right layer to guard.
- The Lambda has no game state, so `"do you have a card"` is answered fuzzy even though Floyd
  carries the lower elevator access card. The original assistant had the identical blind spot.
  Only fixable by passing inventory/room context into the call from the C# side.

## Status / TODO
- [x] Code migrated, `pytest tests/` green (14 tests).
- [x] Prompt reconstructed and tuned against the corpus; game-state, repetition, and voice
      batteries green on gpt-4o (see above).
- [ ] Deploy (SAM/zip) — not done here.
- [ ] After deploy: remove the dead `OPENAI_*_ASSISTANT_ID` env vars; rotate `OPENAI_API_KEY`
      and move it to Secrets Manager (it is plaintext in the Lambda env).
- [x] C#-side follow-ups: door phrasings landed in arsindelve/ZorkAI#564; `"shiny"` decided
      (keep, ZIL-canonical). #564 also carries a ZIL-fidelity fix found along the way — no
      fromitz-board grant before Floyd has actually been through the door and found it.
