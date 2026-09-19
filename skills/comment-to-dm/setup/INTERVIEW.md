# Guided setup: interview the user, then build their first campaign

You are setting up a comment-to-DM campaign for someone who has not used this
skill before and does not want to read the manual. Run this as a conversation.

**Conduct the interview in whatever language the user writes to you in.**

## The rules you do not get to break

1. **Ask one question at a time.** Wait for the answer. Do not dump the whole
   questionnaire and ask them to fill it in.
2. **Nothing real happens until they say yes.** Every call that creates,
   activates or deletes something on their account gets shown as `--dry-run`
   first, in plain language, and waits for an explicit go.
3. **Never print their API key back to them**, not in a message, not in a code
   block, not in a summary. It goes into `.env` and is never echoed.
4. **Do not write the key anywhere except `.env`.** Not into `config.json`, not
   into a script, not into a note file.
5. **Do not invent their copy.** Offer a draft, let them change it. The whole
   point is that it sounds like them.
6. **Refuse an unsafe keyword** and explain why, in §3. This is not a warning
   you pass along, it is a stop.
7. **Do not report success on something you have not run.** "Created" means you
   called the API and read the response back.

## 0. Check the ground before you ask anything

Run these yourself, quietly, and only raise what fails:

```bash
ls ~/.claude/skills/comment-to-dm/scripts/keyword_dm.py   # skill is installed
python3 --version                                          # 3.9+
ls ~/.claude/skills/comment-to-dm/.env                     # key already there?
ls ~/.claude/skills/comment-to-dm/config.json              # already configured?
```

- **No skill folder:** the zip was not unpacked into `~/.claude/skills/`. Fix it,
  then tell them to restart Claude Code, because skills load at startup.
- **`config.json` already exists:** stop. Ask whether they want to add a second
  campaign to it or start over. Never overwrite it. Back it up first either way:
  `cp config.json config.json.bak.$(date +%s)`.

## 1. The key

Ask them to create an API key in their Zernio account settings and paste it.

Write it without ever echoing it:

```bash
cd ~/.claude/skills/comment-to-dm
printf 'LATE_API_KEY=%s\n' 'THE-KEY' > .env
chmod 600 .env
```

Then explain the chmod in one sentence: it makes the file readable only by them,
and an API key is a password to every social account connected to that Zernio
account.

**One warning worth giving here:** if their home folder is on an external or
network drive, background jobs will fail silently later, because macOS blocks
launch agents from those volumes. It works by hand and dies on a schedule, which
looks exactly like a code bug and is not one.

Now prove the key works before building anything on top of it:

```bash
python3 scripts/keyword_dm.py accounts
```

**The first call against any API should be a read, not a write.** If it errors,
the key is wrong or the account is not connected, and they find out now instead
of after half a funnel exists. Show them the account table it returns. If
Instagram is missing from it, they either did not connect it in Zernio or the
account is personal rather than Business/Creator, and nothing downstream can work
around that.

Copy the ids out of that output. **Never type an id by hand.**

## 2. What they are giving away

Four questions, one at a time:

1. What are you sending people? (name it: a guide, a template, a discount code)
2. What is the link?
3. Which post is this for? If it is not published yet, say so, that changes §7.
4. What is your Instagram handle?

Open the link and check it loads. A funnel that delivers a 404 is worse than no
funnel, and they cannot re-send.

## 3. The keyword, which is where accounts get hurt

Ask what word people should comment.

Then **check it, out loud, before accepting it:**

- **How long is it?** Four characters or fewer must never be substring-matched.
  The audit fails on this and so should you.
- **Does it live inside other words?** In languages where prefixes attach to the
  word, substring matching is usually correct, which makes this more dangerous,
  not less. Say the risky collisions out loud.
- **Would someone type it without wanting anything?** If the keyword is a normal
  word in the topic of the post, ordinary comments will trigger it, and people who
  asked for nothing will get a DM. That is precisely what gets reported as spam,
  and spam reports are what close accounts. The API is not the risk.
- **Does it collide with a campaign they already run?** Check:
  ```bash
  python3 scripts/keyword_dm.py ig-list
  ```

Pick the match mode from that, not from habit: `exact` if the word is short or
common, `word` for whole-word matching, `contains` only for a long distinctive
word.

If the keyword is unsafe, **say no and propose two better ones.** Do not write it
into the config with a warning attached.

## 4. The follow gate, or not

Ask: do you want to require a follow before the link, or just send it?

Both are fine. No gate is one message and converts better; a gate trades some of
that for followers. Their call, and they can change it later.

If they want the gate, tell them the one thing that makes it not feel like a toll:
**give explicit permission to leave.** "And if this does not help you, unfollow
with my blessing." It costs nothing, because anyone who resented the gate was
never going to stay.

## 5. Write the config

Copy the example and fill it from their answers:

```bash
cp config.example.json config.json
```

Draft the copy for them, then show it and let them rewrite it. Three things
decide whether it works, and they matter more than anything technical here:

1. **Message one gives, it does not ask.** Never "tap to prove you are not a
   bot". That spends the first message taking something. The button exists for a
   technical reason (DMs from non-followers land in Message Requests, where real
   buttons render and quick-reply chips do not), so frame it as claiming the
   prize: "here it is, tap to get it".
2. **The button title is capped at 20 UTF-16 units** by Meta, and an emoji costs
   two. It must not be a substring of any other live campaign's button title, and
   none may be a substring of it, or one tap fires two funnels and the person
   lands in the wrong one. Check the live triggers before you settle on it:
   ```bash
   python3 scripts/keyword_dm.py flow-list
   ```
3. **The last message opens a conversation, not just a link.** "Stuck, or got a
   question? Write to me here." Replies are the cheapest signal the platform reads
   as a real relationship, and it is where the real questions arrive.

Leave `link_tracking` off. A redirect wrapper around a link is a spam heuristic
inside DMs.

Then run the audit and show them the output:

```bash
python3 scripts/keyword_dm.py audit
```

It must pass before you create anything. If it fails, fix the config, do not
explain the failure away.

## 6. Dry run, show, then create

Both halves, dry first:

```bash
python3 scripts/keyword_dm.py ig-create   <campaign> --dry-run
python3 scripts/keyword_dm.py flow-create <campaign> --dry-run
```

Explain in their words what the person on the other end will actually see:
the comment, the DM, the button, the gate, the link. Not the JSON.

**Tell them the structural thing here, because it confuses everyone once:** this
is two separate features joined at the button. The comment and first DM are a
comment automation. Everything after the button tap is a workflow. The workflow
builder has no comment trigger and never did; that is not a setting anyone is
failing to find.

On their go:

```bash
python3 scripts/keyword_dm.py ig-create   <campaign> --post-id <platform post id>
python3 scripts/keyword_dm.py flow-create <campaign>
python3 scripts/keyword_dm.py flow-activate <workflowId>
python3 scripts/keyword_dm.py audit
```

Get the post id from `posts --platform instagram`, never by hand.

**Always pass `--post-id`.** An account-wide rule means someone commenting on a
post from two years ago is pulled into a funnel that has nothing to do with it.
Only `story_reply` rules belong account-wide, because a story has no post to
scope to.

If the post is not published yet, create the rule account-wide **and** start
`scripts/rescope_on_publish.py`, which binds it to the post the moment it goes
live. Do not leave it account-wide.

## 7. Make them test it, and tell them why a bad test looks like a pass

Three conditions. Miss one and the test proves nothing:

- **Comment from a different account.** Their own comment on their own post
  triggers nothing at all.
- **The rule has to exist before the comment.** The window to answer a comment
  privately is counted from the comment, so a rule created afterwards has nothing
  to answer.
- **Pick a post with no rule of its own.** A post-scoped rule wins on its post, so
  an account-wide rule goes silent there and "suppressed" is indistinguishable
  from "broken".

Then read the result from the API, not from their word for it:

```bash
python3 scripts/keyword_dm.py ig-logs  <automationId>   # who commented, what they wrote, did it send
python3 scripts/keyword_dm.py flow-runs <workflowId> --vars
```

Read `variables`, not the node the run is parked on. Every node has a failure
edge, so a completed run can look like a total loss when it is not.

**A story reply is the best free smoke test.** It is a separate dispatch path, so
it proves nothing about the comment trigger, but it exercises everything
downstream (matching, DM copy, button rendering, workflow routing, follow gate,
link delivery) without needing a post at all. Use it to tell a broken trigger
apart from a broken funnel.

Close by telling them the one rule that makes testing non-optional:
**one private reply per comment, ever.** The platform allows exactly one. If the
first DM went out broken, there is no second attempt for that person.

## 8. Hand it over

Tell them, in two lines:

- Run `audit` after every change. `config.json` drives the YouTube poller while
  the live rule drives Instagram, so the two drift silently and tightening one
  side leaves the other dangerous.
- To change the campaign later, edit `config.json` and ask Claude to re-run
  `ig-create`/`flow-create`. To add a second one, add another object to `rules`.

Then stop. Do not offer to build more of the funnel unless they ask.
