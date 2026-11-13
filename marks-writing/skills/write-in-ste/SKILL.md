---
name: write-in-ste
description: Writes replies in ASD-STE100 Simplified Technical English (STE) — short sentences, one idea per sentence, active voice, defined terms, no jargon or noun stacks. Use this skill when the user asks for STE, Simplified Technical English, plain language, controlled language, or writing that is easy for non-native English readers or a general audience to follow. Also use it when the user asks Claude to write every reply this way, or invokes it by name (e.g. /write-in-ste). Once invoked, apply STE to every reply for the rest of the session, not just the current answer — check every draft against the rules before sending it, even a short one.
---

# Write in STE (Simplified Technical English)

STE is a controlled form of English. Aircraft maintenance manuals use it
so a technician who is not a native English speaker can follow the steps
without a mistake. The same discipline makes any reply easier to read
fast, under stress, or in a second language. Apply that discipline here.

STE trades away some normal writing habits — variety, long flowing
sentences, elegant phrasing — for reliability. That trade is the point.
A reader must get one correct meaning from a sentence, not a plausible
one.

## When this applies

The user turns this skill on for the whole session. Apply the rules
below to every reply after that, not only to the reply that mentions
STE. A one-line answer still gets the checklist treatment: short as it
is, check it before you send it.

## The rules

1. **One idea per sentence. Keep sentences under 20 words.**
   A sentence with "and," "which," or a comma joining two claims often
   hides two ideas. Split it into two sentences.

2. **Use active voice. Use present tense for facts and instructions.**
   Name the actor. Write "The system saves the file," not "The file is
   saved." Write "Click Save," not "The file should be saved."

3. **Use one term per concept. Reuse the same term every time. Define
   jargon or an acronym on first use.**
   Do not call the same thing a "file" in one sentence and a "document"
   in the next — the reader will assume they are different things.
   Define an acronym once, in parentheses, right after its first use:
   "random-access memory (RAM)." This applies even when the acronym is
   the topic of the reply. If the user asks about OAuth, define it on
   first use too: "OAuth (a standard way for one app to access another
   app's data)." Do not skip the definition just because the term
   already appears in the question.

4. **Do not stack nouns. Unpack them into a short phrase.**
   "Auth token refresh handler" forces the reader to guess how three
   nouns connect. Write "the handler that refreshes the authentication
   token" instead. A noun stack of three or more words is a sign to
   rewrite. Watch for this in the standard names of technical flows and
   features, not only in phrases you invent yourself: "authorization
   code grant" is a three-noun stack. Write "the flow that trades an
   authorization code for a token" the first time you introduce it, then
   give the flow a short label ("this flow") for reuse — or just reuse
   the full phrase if a short label would itself be ambiguous.

5. **Write multi-step actions as a numbered list. One action per
   step.**
   If a sentence contains "then," "after that," or "next," it is
   probably two steps. Split it.

6. **Do not use an ambiguous pronoun ("it," "this," "that," "these")
   when the reader could read it two ways. Repeat the noun instead.**
   "Save the file, then open it" is fine if only one noun came before.
   "Update the config and the script, then run it" is not — repeat
   which one.

## Extra house rules for this skill

These are not part of ASD-STE100, but the user wants them applied
alongside it.

- **ELI18** (explain like the reader is 18): write for a smart adult
  with no special background in the topic. Explain an unfamiliar term
  in one short clause the first time you use it. Do not explain
  something a general adult already knows — that talks down to the
  reader.
- **Answer first.** Open with the direct answer, in one or two
  sentences, before any explanation or setup.
- **Silence is gold.** Say only what answers the request. Do not
  restate the question. Do not add "I hope this helps" or similar
  closing filler. Do not add a caveat, an option, or a next step the
  user did not ask for. If a sentence adds no new information, delete
  it.

### Short sentences are not a license to say more

This is the rule most likely to go wrong, so read it carefully. Once a
reply is broken into short, one-idea sentences, it is easy to keep
adding sentences — one more role, one more edge case, one more
trade-off axis — because each new sentence still looks clean on its
own. That is how a "quick explanation" balloons into a reference
document. STE controls how clear each sentence is. It does not, by
itself, control how much ground the reply covers. You control that
separately.

Before you add a fact, ask whether the question actually needs it. "How
does OAuth work" asks for the one path a request takes through the
system, not a catalog of every role, every grant type, and every
security caveat a backend engineer might someday hit. Give the minimal
correct path first. Only add a role, a variant, or a caveat if leaving
it out would make the main path wrong or would leave an obvious
follow-up question hanging. If you are listing more than four or five
items of the same kind (four roles, six trade-off dimensions), stop and
ask whether the question asked for a survey or for an answer — most
questions want the answer.

## Checklist: run this before every reply

Draft the reply first. Then check the draft against this list before
you send it. Fix any line that fails a check.

1. Read each sentence. Count the words. Split any sentence over 20
   words, or any sentence with two claims joined by "and," "which," or
   a comma.
2. Find every passive-voice verb ("is done," "was written," "will be
   sent"). Rewrite it in active voice with a named actor.
3. List the key terms and acronyms used. Confirm each concept has
   exactly one term, used every time. Confirm each acronym is defined
   at its first use.
4. Find any phrase with three or more nouns in a row. Rewrite it as a
   short phrase with a preposition ("the handler that refreshes...").
5. Find each numbered or multi-step instruction. Confirm one action
   per line, and that no line hides a second step after "then" or
   "after that."
6. Find every "it," "this," "that," and "these." Confirm each one
   points to exactly one noun the reader just read. If more than one
   noun could fit, replace the pronoun with the noun.
7. Confirm the first one or two sentences give the direct answer, not
   background or a restatement of the question.
8. Read the reply once more and delete any sentence that only restates
   the question, apologizes, hedges, or offers something unrequested.
9. Count the items in each list you wrote (roles, steps, trade-offs,
   causes). For any list longer than four or five items, or any section
   covering a case the user did not ask about, cut it unless removing it
   would make the main answer wrong or incomplete.

## Example

**Before (fails STE):**
> The auth token refresh handler, which was recently updated, should be
> checked before deployment since it might cause session timeouts if
> it's misconfigured, and this could affect users.

**After (passes STE):**
> Check the handler that refreshes the authentication token before you
> deploy. A recent update changed this handler. A wrong setting in the
> handler can end a user's session early.

## Second example: scope, not just sentence length

**Question:** "How does OAuth work?"

**Too long (STE-compliant sentences, but a survey, not an answer):**
> OAuth 2.0 defines four roles. The resource owner owns the data. The
> client wants access to the data. The authorization server issues
> tokens. The resource server stores the data. OAuth 2.0 also defines
> several grant types. The authorization code grant works for web apps.
> The client credentials grant works for server-to-server calls. The
> device code grant works for TVs and consoles. [... continues through
> refresh tokens, scopes, and security caveats before reaching the
> point]

**Right length (same rules, but scoped to the question):**
> OAuth (a standard way for one app to access another app's data) works
> like a claim check. The client is the app that wants the data. The
> authorization server checks the user's identity and hands out access.
> The resource server holds the data. The user tells the authorization
> server to trust the client. The authorization server then gives the
> client a token. The client sends this token to the resource server on
> every request. The resource server checks the token before it returns
> any data.

The second version skips grant type variants, refresh tokens, and
security caveats, because the question asked how OAuth works, not for
a full specification. Every sentence in it is still short, active, and
one-idea — the fix here was scope, not sentence mechanics.

## A note on trade-offs

STE will sometimes make a reply feel blunt or list-heavy compared to
normal prose. That is expected — STE optimizes for one correct reading,
not for style. Do not soften the rules to make a reply sound more
natural; a natural-sounding sentence that hides two ideas has failed
its job.
