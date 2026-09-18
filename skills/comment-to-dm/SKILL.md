---
name: comment-to-dm
description: Comment a keyword on a post, get the link in a DM automatically (the ManyChat pattern), via the Zernio API. Use when setting up, editing, auditing or debugging a "comment WORD and I'll send you the link" campaign on Instagram or YouTube.
---

# Comment → DM

Someone comments a keyword under your post and gets the link automatically.
Instagram gets a real DM with buttons; YouTube gets a public reply, because
YouTube has no DM system at all; TikTok is not possible.

Everything runs on the Zernio API. No monthly ManyChat bill, and no scraping:
these are the official endpoints, driven by your own key.

## Setup, once

1. **Get a Zernio account** with the Instagram account connected. The Instagram
   account has to be a Business or Creator account. A personal account exposes
   neither comments nor messages, and nothing here can work around that.
2. **Make an API key** in Zernio's settings.
3. **Put it next to this skill**, not in the code:

   ```bash
   echo 'LATE_API_KEY=your_key_here' > ~/.claude/skills/comment-to-dm/.env
   chmod 600 ~/.claude/skills/comment-to-dm/.env
   ```

   A key on an external or removable drive works when you run a command by hand
   and fails silently on every scheduled run, because macOS blocks background
   agents from those volumes. Keep it here.
4. **Copy the config and fill it in:**

   ```bash
   cd ~/.claude/skills/comment-to-dm
   cp config.example.json config.json
   python3 scripts/keyword_dm.py accounts     # read your ids from here, never type them
   ```

`config.json` is the only file with anything personal in it, and it is
gitignored. Everything in `config.example.json` is a placeholder.

## Platform reality

| | trigger | delivery | how |
|---|---|---|---|
| **Instagram** | comment or story reply | **DM**, up to 3 buttons, plus an optional public reply | Zernio's native engine, webhook driven, instant. Register once. |
| **YouTube** | comment | **public reply** under the comment | Polled by `yt-run`. YouTube has no DMs, and Zernio emits no YouTube comment webhook. |
| **TikTok** | | | **Not possible.** Zernio has no TikTok comment or DM API and TikTok's public API exposes neither. ManyChat's own TikTok comment-to-DM is live in three countries in south-east Asia and nowhere else. The only play is asking viewers to DM the word, or pinning a comment with the link. Do not promise it in a video. |

## The funnel is two features, not one

This is the thing that confuses everyone the first time, and it is worth knowing
before you go looking for a setting that does not exist.

1. **Comment → first DM** is a *comment automation* (`ig-create`). That first DM
   carries a `postback` button, and the button is not decoration: DMs from people
   who do not follow you land in Message Requests, where quick-reply chips do not
   render and real buttons do.
2. **Button tap → follow gate → link** is a *workflow* (`flow-create`). A tap
   arrives as an ordinary inbound message carrying the button's title, so the
   workflow just triggers on that text.

**The workflow builder has no comment trigger.** Its triggers are inbound
message, API call and WhatsApp event. A ManyChat-style funnel is therefore always
these two pieces joined at the button.

And one API shape to know: a workflow's `send_message` node can only push text or
media on Instagram, because `interactive` is WhatsApp only. Anything with buttons
goes out through a `webhook` node calling
`POST /v1/inbox/conversations/{id}/messages`, and its `bodyTemplate` has to be a
JSON **string**, not an object. `build_flow_graph` in `keyword_dm.py` already does
this; the note is here for when you extend it.

## Copy that works

Three moves, in this order. They matter more than anything technical on this page.

1. **Message one gives, it does not ask.** Not "tap to prove you are not a bot",
   which spends your first message taking something. Restate the prize and let the
   button claim it.
2. **If you gate on a follow, give permission to leave.** "And if this does not
   help you, unfollow with my blessing." It costs nothing, because anyone who
   would have resented the gate was never going to stay, and it turns a toll into
   an offer.
3. **The last message opens a conversation, not just a link.** "Stuck, or got a
   question? Write to me here." Replies are the cheapest signal the platform reads
   as a real relationship, and it is where real questions arrive.

## Commands

```bash
cd ~/.claude/skills/comment-to-dm

python3 scripts/keyword_dm.py accounts                       # ids, and a sanity check on the key
python3 scripts/keyword_dm.py posts --platform instagram     # recent posts + their platform post ids

python3 scripts/keyword_dm.py ig-create my-campaign --post-id 179...   # scoped to one post
python3 scripts/keyword_dm.py ig-create my-campaign --dry-run
python3 scripts/keyword_dm.py ig-list
python3 scripts/keyword_dm.py ig-logs <automationId>         # who commented, what they wrote, did it send
python3 scripts/keyword_dm.py ig-delete <automationId>

python3 scripts/keyword_dm.py flow-create my-campaign --dry-run   # read the graph first
python3 scripts/keyword_dm.py flow-create my-campaign
python3 scripts/keyword_dm.py flow-activate <workflowId>
python3 scripts/keyword_dm.py flow-runs <workflowId> --vars       # debug a real tap
python3 scripts/keyword_dm.py flow-pause <workflowId>
python3 scripts/keyword_dm.py flow-list

python3 scripts/keyword_dm.py yt-run --dry-run               # always dry-run first
python3 scripts/keyword_dm.py yt-run
python3 scripts/keyword_dm.py yt-status

python3 scripts/keyword_dm.py audit                          # run this after ANY change
```

## Testing, and why a bad test looks like a pass

Three conditions. Miss one and the test tells you nothing.

- **Comment from a different account.** Your own comment on your own post
  triggers nothing.
- **The rule must exist before the comment.** The window to answer a comment
  privately is counted from the comment, so a rule created afterwards has nothing
  to answer. For a scheduled post, create the rule account-wide and run
  `scripts/rescope_on_publish.py`, which binds it to the post the moment it
  publishes.
- **Pick a post with no rule of its own.** A post-scoped rule wins on its post, so
  an account-wide rule goes silent there and you cannot tell "suppressed" from
  "broken".

A **story reply** is the best free smoke test. It is a separate dispatch path from
comments, so it proves nothing about the comment trigger, but it exercises
everything downstream (matching, DM copy, button rendering, workflow routing,
follow gate, link delivery) without needing a post at all. Use it to tell a broken
trigger apart from a broken funnel.

## Safety, which is the part that protects your account

The thing that gets an account actioned is **spam reports**, not the API. Official
endpoints with your own OAuth keep you compliant. Messaging people who never asked
is what does the damage, and every rule below exists to prevent exactly that.

- **Never `contains`-match a short keyword.** In Hebrew prefixes attach to words,
  so substring matching is usually right, but a keyword of four characters or
  fewer will fire inside unrelated words. The audit fails on this.
- **Scope comment rules to their post.** Account-wide means someone commenting on
  a post from two years ago is pulled into a funnel that has nothing to do with it.
  Only `story_reply` rules belong account-wide, because a story has no post to
  scope to.
- **Keep link tracking off.** A redirect wrapper around a link is a spam heuristic
  in DMs.
- **`--max-words 2` on YouTube, and leave it there.** The poller reads *every*
  comment on the video, so a bare keyword match also catches jokes, complaints and
  people just discussing the topic. Auto-replying to those with a promo link is
  what earns reports.
- **The YouTube poller is the only genuinely risky surface**, because it is your
  code and it posts publicly. It ships capped: 5 replies per run, a hard 60 per
  day counted from the state file, and jittered 8 to 20 second gaps. Do not raise
  those without a reason.
- **One private reply per comment, ever.** The platform allows exactly one. If your
  first DM went out broken, there is no second attempt for that person. This is
  why the test above is not a formality.
- **Run `audit` after every change.** `config.json` drives the YouTube poller while
  the live rule drives Instagram, so the two drift silently: tightening one side
  leaves the other dangerous. The audit is what catches it.

## Debugging, in the order that finds it fastest

- **Map posts to connections first.** A comment webhook is routed to the
  connection that *published* the post. If you reconnected an account, the old
  connection can stay alive beside the new one, and a rule on one of them has
  literally nothing to listen to. `posts` shows which connection owns each post.
- **A rule bound to a removed connection dies.** Split the last-log time by account
  whenever a funnel looks broken.
- **`accountId` is immutable on a comment automation.** Moving one to another
  connection means delete and recreate, which resets stats and drops the DM logs.
  Archive `ig-logs` first.
- **Read `variables`, not the current node.** Every node has a failure edge, so a
  run parked at the exit looks like a total loss when it is not. The variable bag
  carries the result of each send. "Did this person get it" is: did they confirm
  the gate, and did the link send succeed.
- **`executions` pagination is unreliable.** The limit caps at 100 and the offset
  is ignored, so a naive loop re-reads page one and invents duplicate failures.
  Dedupe by execution id.
- **Before tightening a match, read the logs.** They carry the comment text.
  Checking what people actually typed beats reasoning about the tokenizer.

## Optional: run the YouTube poller on a schedule

`launchd/yt-keyword-reply.plist.template` is a macOS agent that runs `yt-run`
every 15 minutes. Replace every `REPLACE-ME` in it, then:

```bash
cp launchd/yt-keyword-reply.plist.template ~/Library/LaunchAgents/com.you.yt-keyword-reply.plist
launchctl load ~/Library/LaunchAgents/com.you.yt-keyword-reply.plist
```

Its stdout log stays empty even on success. `yt-status` and `state/yt_replied.json`
are the source of truth, and the `.err.log` is where failures go.

## Making it yours

This is a starting point, not a finished product. The obvious next moves: more
steps after the link, branching on what someone replies, a second gate for a
different offer, or writing the results somewhere you can read them. The script is
one file and every subcommand is a small function; ask Claude to read
`scripts/keyword_dm.py` and add what you need.

MIT licensed. Built by Xplain, [explain.co.il](https://explain.co.il).
