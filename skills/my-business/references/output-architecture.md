# Output architecture

Choose the smallest structure that keeps future sessions accurate and easy to navigate.

## Quick file

Create or merge a root `CLAUDE.md` with these sections when relevant:

1. `# Name or business`
2. `## What this is`
3. `## Read order`
4. `## Business`
5. `## Offers`
6. `## Audience`
7. `## Voice`
8. `## Hard rules`
9. `## Tools and sources of truth`
10. `## Current priorities`
11. `## Key files`

Keep it under 200 short lines. Omit empty sections and long examples.

## Organized brain

Create only the notes supported by actual information:

```text
CLAUDE.md
Home.md
Business/
  Overview.md
  Offers.md
  Audience.md
  Voice.md
  Proof.md
Personal/
  Profile.md
Operations/
  Tools.md
  Workflows.md
Projects/
  Project Name.md
People/
  Person Name.md
Knowledge/
  Examples.md
```

### Root CLAUDE.md

The root file should contain:

- A short identity and purpose statement
- The exact read order
- Stable hard rules and approval boundaries
- Current top priorities with dates
- A compact folder map
- Instructions to read only relevant linked notes
- A rule to update the correct project note when facts or decisions change

Do not duplicate detailed note content in the root file.

### Home.md

Make `Home.md` a human-readable map of the vault. Link active projects, business notes, personal context, operations, people, and examples. Include a short "Start here" explanation.

### Business notes

- `Overview.md`: identity, mission, positioning, markets, public links
- `Offers.md`: one section per active offer; separate planned and retired offers
- `Audience.md`: customer groups, pains, attempts, objections, exclusions
- `Voice.md`: rules plus real examples and channel differences
- `Proof.md`: only verified claims, evidence, testimonials, and case studies

### Personal note

Create `Personal/Profile.md` only with explicit consent. Keep it separate from business context and include only information the user wants Claude to use.

### Operations notes

- `Tools.md`: tool name, purpose, relevant non-secret identifiers, and source of truth
- `Workflows.md`: recurring processes, triggers, outputs, quality gates, and handoffs

### Project notes

Use one note per active project with:

- Objective
- Owner and collaborators
- Current state with an absolute date
- Decisions
- Blockers
- Next step
- Relevant files and links

### People notes

Create a person note only when the relationship affects work. Record role, responsibilities, communication context, and confirmed preferences. Avoid speculation.

### Examples

Store representative examples or links in `Knowledge/Examples.md`. Label each example by type, date, result, and why it is useful.

## Merge behavior

When files already exist:

- Read before writing.
- Preserve information that remains true.
- Prefer targeted edits over a full rewrite.
- Do not remove a rule, project, or source without explaining why.
- Resolve contradictions with the user.
- Mark obsolete offers or projects as retired or archived instead of erasing history.

