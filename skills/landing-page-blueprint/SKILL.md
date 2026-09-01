---
name: landing-page-blueprint
description: Plan and build a converting Hebrew RTL landing page: section order, layout decisions, and implementation rules for a dark or light one-pager. Use when asked to design or build a landing page ("תבנה לי דף נחיתה", "עיצוב דף מכירה") before or alongside writing its copy.
---

# Landing Page Blueprint

You design and build Hebrew RTL landing pages that convert. Copy comes first:
if no copy exists yet, run the sales-page-copy skill (or ask for the copy)
before designing; a page designed around lorem ipsum gets rebuilt when the
real words arrive.

## Step 1: Three decisions before any code

Ask, or infer and state your choice:

1. **טמפרטורת הטראפיק:** קר (מודעה ראשונה) = דף ארוך שבונה אמון; חם (רשימת
   תפוצה, קהילה) = דף קצר שמגיע מהר להצעה.
2. **הפעולה האחת:** השארת פרטים, רכישה, או הרשמה לאירוע. הדף בנוי סביבה
   ואין בו שום פעולה מתחרה: בלי תפריט, בלי קישורים החוצה, בלי פוטר עמוס.
3. **עולם ויזואלי:** כהה-פרימיום או בהיר-נקי, צבע מותג אחד + צבע פעולה אחד.
   צבע הפעולה מופיע רק על CTA ועל הדגשות ספורות; אם הכל צבעוני, כלום לא בולט.

## Step 2: The section stack

Order for a cold-traffic page (cut sections for warm traffic, keep order):

1. פתיח: הבטחה, תת-כותרת, CTA, ורמז ויזואלי למוצר. גובה מסך אחד במובייל.
2. פס אמון דק: לוגואים, מספר לקוחות, או שורת עדות אחת.
3. הכאב והמפנה.
4. ההצעה: כרטיס לכל רכיב, אייקון אמוג'י או מספר, תועלת בכל כותרת.
5. עדויות: וידאו חזק מטקסט, טקסט עם שם ותמונה חזק מציטוט אנונימי.
6. מי אנחנו: קצר, עם תמונה אמיתית; בונה אמון, לא ביוגרפיה.
7. מחיר + הסרת סיכון.
8. שאלות ותשובות באקורדיון.
9. סגירה: ההבטחה + דחיפות + CTA אחרון, ו-CTA דביק במובייל לאורך כל הדף.

## Step 3: Implementation rules

- **RTL היא ברירת המחדל:** `dir="rtl"` על השורש. כל מחיר, מספר טלפון או פקודת
  קוד עטופים באלמנט עם `direction:ltr; unicode-bidi:isolate`, אחרת הסימן קופץ
  לצד הלא נכון.
- **מובייל קודם:** בונים את עמודת ה-375px קודם ומרחיבים; רוב הטראפיק שם.
  כפתור ראשי ברוחב מלא במובייל, גובה מגע 48px לפחות.
- **טיפוגרפיה:** משפחת גופן אחת, כותרות במשקל כבד, גוף 17-18px, שורה 1.6-1.75.
  כותרת H1 אחת בדף.
- **תנועה:** אנימציות כניסה עדינות שרצות פעם אחת (once), לעולם לא בשני
  הכיוונים; לכבד `prefers-reduced-motion`. תנועה מושכת עין אל ה-CTA, לא
  מתחרה בו.
- **טפסים:** מינימום שדות, ולידציה בעברית, honeypot נסתר, והודעת הצלחה שאומרת
  מה קורה עכשיו ("שלחנו לך מייל, בדקו גם בספאם").
- **ביצועים:** תמונות בגודל אמיתי וב-lazy loading, בלי ספריות אייקונים,
  פונט מקומי עם fallback. דף שנטען לאט הוא דף שלא ממיר.
- **נגישות:** אלמנטים דקורטיביים עם `aria-hidden="true"`, כפתורים אמיתיים
  ולא div לחיץ, ניגודיות טקסט מספקת גם על רקע כהה.

## Output format

When planning: deliver the section stack as a numbered list with a one-line
content note and a one-line layout note per section, then the three visual
decisions and why.

When building: implement section by section, verify in the browser after
every few sections (desktop and 375px), and finish with a screenshot of the
full page plus a list of any placeholder assets the user still owes
(תמונות, וידאו, לוגואים) marked clearly in the page itself.
