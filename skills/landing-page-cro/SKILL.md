---
name: landing-page-cro
description: Audit a landing page for conversion blockers and deliver a prioritized fix list with rewritten copy for the worst offenders. Use when asked to improve conversions, review a landing page, or diagnose why a page gets traffic but no leads ("שיפור המרות", "למה אין לידים").
---

# Landing Page CRO Audit

You audit landing pages for conversion and deliver fixes, not observations.
Every finding must name the element, say why it costs conversions, and show
the fix; "השורה הזו חלשה" without a rewrite is not a finding.

## Getting the page

If given a URL, fetch it and read the real rendered copy. If given a
screenshot or pasted copy, work from that and say which checks you could not
run (speed, mobile, form behavior). Always check the mobile layout when you
have browser access; most Israeli landing page traffic is mobile.

## The audit, in scoring order

Work through the five gates in order. A failure at an earlier gate makes the
later ones irrelevant, which is exactly how a visitor experiences the page.

### Gate 1: Five-second clarity
Look at the above-the-fold area only, for five seconds. Can you answer: what
is offered, for whom, and what happens if I click? If any answer is missing,
that is finding #1 regardless of what else is on the page. The headline must
name a result, not the product's category.

### Gate 2: The promise-audience match
Does the pain and promise language match one specific reader? A page that
speaks to "כל מי שרוצה להתקדם" converts no one. Check that the first third of
the page uses words the customer would use, not the seller's jargon.

### Gate 3: Friction
- Form fields: every field beyond name/email/phone must justify itself.
- Number of decisions before the CTA: multiple competing buttons, menu links,
  outbound links. A funnel page has one exit.
- CTA copy: does the button say what you get ("שלחו לי את המדריך") or what
  you must do ("שליחה")?
- Load and layout: broken sections, walls of text, autoplaying noise.

### Gate 4: Trust
- Real proof near the decision points, with names and identifying details.
- Price presented once, anchored, with risk reversal beside it.
- Signs of a live business: real photos, contact details, terms.
- Nothing that overclaims; one inflated promise poisons the true ones.

### Gate 5: Mobile
- Above-the-fold on a phone: does the promise + CTA survive without scrolling?
- Tap targets, form usability, sticky CTA presence on long pages.
- Hebrew RTL rendering: prices and phone numbers as single LTR tokens,
  punctuation on the correct side.

## Output format

1. **ציון כולל** out of 10, one sentence of justification.
2. **שלושת התיקונים ששווים הכי הרבה כסף** with before/after copy for each,
   ordered by expected impact, each labeled by gate.
3. **רשימת הממצאים המלאה** as a table: אלמנט, הבעיה, התיקון, עדיפות (P0-P2).
4. If asked to implement: fix P0s first, one commit-sized change at a time,
   and re-check the page after each.

Write all customer-facing rewrites in Hebrew with no em dash and no empty
superlatives, and never add numeric promises about future results.
