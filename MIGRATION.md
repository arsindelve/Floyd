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

## Status / TODO
- [x] Code migrated, `pytest tests/` green (14 tests).
- [x] Reconstructed prompt evaluated against the full prod corpus; game-critical intents
      (`take board`→PickUp, `go north`→GoSomewhere) classify correctly.
- [ ] Voice tuning — see flagged divergences from the corpus eval (repetitive object-declines,
      over-eager PickUp on non-object "take"s, meta-question sameness). Deliberately left for a
      later pass.
- [ ] Deploy (SAM/zip) — not done here.
