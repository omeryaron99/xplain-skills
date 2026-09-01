# Xplain Skills

הסקילים של סדנת Claude Code של עומר ומתן ([Xplain](https://explain.co.il)).

כל תיקייה תחת `skills/` היא סקיל אחד ל-Claude Code. ההתקנה הנוחה ביותר היא דרך
[מרכז הסקילים של הסדנה](https://explain.co.il/claude-code/skills), שם כל סקיל
מגיע עם הסבר, דוגמה ופקודת התקנה מוכנה להעתקה.

## התקנה ידנית של סקיל בודד

```bash
curl -sL https://github.com/omeryaron99/xplain-skills/archive/main.tar.gz | tar -xz -C /tmp && mkdir -p ~/.claude/skills && cp -r /tmp/xplain-skills-main/skills/<skill-name> ~/.claude/skills/ && rm -rf /tmp/xplain-skills-main
```

החליפו את `<skill-name>` בשם התיקייה של הסקיל, ופתחו שיחה חדשה ב-Claude Code.

## למתחזקים

`scripts/build-skills-repo.py` אורז את הסקילים מהמכונה של עומר לתוך `skills/`,
מנקה קבצים שאינם שייכים לכאן ומריץ סריקת אבטחה. הרצה מחדש היא הרענון; קומיט
ודחיפה נעשים ידנית אחרי קריאת פלט הסריקה.
