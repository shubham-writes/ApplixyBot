"""
Message templates for ApplixyBot — MarkdownV2 formatted.
All bot-facing text lives here to keep handlers clean.
"""
from utils.helpers import escape_md


# ──────────────────────────────────────────────
# Onboarding
# ──────────────────────────────────────────────

def welcome_message() -> str:
    return (
        "🤖 *Welcome to ApplixyBot\\!*\n\n"
        "I help frontend developers find jobs, write cover letters, "
        "and auto\\-apply — all inside Telegram\\.\n\n"
        "Let's set up your profile in 2 minutes\\.\n\n"
        "What best describes you?"
    )


def skills_prompt() -> str:
    return "Great\\! Which technologies do you work with?\n\\(Select all that apply, then tap *Done*\\)"


def onboarding_complete(skills: list[str], location: str, has_resume: bool) -> str:
    skills_text = escape_md(", ".join(skills)) if skills else "None selected"
    loc_map = {"remote": "🌏 Remote", "india": "🇮🇳 India", "both": "🌐 Both"}
    loc_text = loc_map.get(location, location)
    resume_text = "✅ Uploaded" if has_resume else "❌ Not uploaded yet"

    return (
        "✅ *You're all set\\!*\n\n"
        f"*Skills:* {skills_text}\n"
        f"*Location:* {escape_md(loc_text)}\n"
        f"*Resume:* {resume_text}\n\n"
        "I'll send your first job alerts tomorrow morning\\.\n\n"
        "What would you like to do now?"
    )


# ──────────────────────────────────────────────
# Main Menu
# ──────────────────────────────────────────────

def main_menu(user: dict) -> str:
    plan = user.get("plan", "free")
    limits_text = "5 jobs/day • 1 cover letter/day"
    if plan == "pro":
        # Check plan expiry
        expires_at = user.get("plan_expires_at")
        date_str = expires_at.strftime("%d %b %Y") if expires_at else "auto"
        limits_text = f"unlimited • renews {date_str}"
        
        return (
            "🏠 *ApplixyBot*\n"
            f"Plan: ⭐ Pro \\({escape_md(limits_text)}\\)\n"
        )
    return (
        "🏠 *ApplixyBot*\n"
        f"Plan: Free \\({escape_md(limits_text)}\\)\n"
    )


# ──────────────────────────────────────────────
# Jobs
# ──────────────────────────────────────────────

def compute_match_details(user_skills: list[str], job_skills: list[str], user_exp: str = "0", job_exp: int | None = None) -> dict:
    """Compute a weighted match score: 70% skills + 30% experience."""
    
    # ── Skills Component (70% weight) ──
    if not job_skills:
        skill_pct = 50  # unknown job requirements = neutral
        matched_disp, missing_disp = [], []
    else:
        user_set = set(s.lower() for s in user_skills)
        job_set = set(s.lower() for s in job_skills)
        if not job_set:
            skill_pct = 50
            matched_disp, missing_disp = [], []
        else:
            matched = list(user_set.intersection(job_set))
            missing = list(job_set.difference(user_set))
            skill_pct = int((len(matched) / len(job_set)) * 100)
            
            original_map = {s.lower(): s for s in job_skills}
            matched_disp = [original_map.get(m, m) for m in matched]
            missing_disp = [original_map.get(m, m) for m in missing]
    
    # ── Experience Component (30% weight) ──
    u_map = {"0": 0, "1": 1, "2": 2, "3_5": 4, "5_plus": 6, "5+": 6}
    u_exp_years = u_map.get(str(user_exp), 0)
    
    exp_pct = 50  # default: unknown job requirement
    exp_note = None
    
    if job_exp is not None and job_exp > 0:
        gap = u_exp_years - job_exp
        if gap >= 0:
            exp_pct = 100  # meets or exceeds
            if gap > 2:
                exp_note = f"✅ You exceed the {job_exp}+ yr requirement"
            else:
                exp_note = f"✅ You meet the {job_exp}+ yr requirement"
        elif gap == -1:
            exp_pct = 60  # close
            exp_note = f"⚠️ Requires {job_exp}+ yrs — you have {u_exp_years}"
        else:
            exp_pct = max(0, 100 + (gap * 25))  # steep penalty
            exp_note = f"🔴 Requires {job_exp}+ yrs — you have {u_exp_years}"
    
    # ── Weighted Total ──
    total_score = int(skill_pct * 0.70 + exp_pct * 0.30)
    
    # Severe penalty for massive experience gaps (hard filters)
    if job_exp is not None and job_exp > 0:
        gap = u_exp_years - job_exp
        if gap < -7:
            # Huge gap (e.g. 0-1 yr applying for 10+ yrs)
            total_score = int(total_score * 0.20)
        elif gap <= -5:
            # Major gap (e.g. fresher applying for Senior 5-8+ role)
            total_score = int(total_score * 0.35)
        elif gap <= -3:
            # Significant gap
            total_score = int(total_score * 0.60)
        elif gap == -2:
            # Small gap, minor penalty
            total_score = int(total_score * 0.85)

    total_score = max(0, min(100, total_score))
    
    return {
        "score": total_score,
        "skill_pct": skill_pct,
        "exp_pct": exp_pct,
        "matched": matched_disp,
        "missing": missing_disp,
        "exp_note": exp_note,
        "job_exp": job_exp,
    }

def format_job_list_message(jobs: list[dict], plan: str, total_count: int, user_skills: list[str] = None, user_exp: str = "0") -> str:
    """Format a list of jobs for display."""
    showing = len(jobs)
    header = f"🔍 *Today's Frontend Jobs* \\({showing} of {total_count} available\\)\n"
    header += "━━━━━━━━━━━━━━━━━━━━\n\n"

    lines = []
    nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    for i, job in enumerate(jobs[:5]):
        num = nums[i] if i < len(nums) else f"{i+1}\\."
        title = escape_md(job.get("title", "Untitled"))
        company = escape_md(job.get("company") or "Unknown Company")
        location = escape_md(job.get("location", "Remote") or "Remote")
        salary = escape_md(job.get("salary", "")) if job.get("salary") else ""
        url = job.get("url", "")
        skills_list = job.get("skills", [])
        skills_text = escape_md(", ".join(s.title() for s in skills_list[:6])) if skills_list else ""

        posted = ""
        if job.get("posted_at"):
            from datetime import datetime, timezone
            diff = datetime.now(timezone.utc) - job["posted_at"]
            hours = int(diff.total_seconds() / 3600)
            if hours < 1:
                posted = "⏰ Just now"
            elif hours < 24:
                posted = f"⏰ {hours}h ago"
            else:
                posted = f"⏰ {hours // 24}d ago"

        if url:
            line = f"{num}  [{title}]({url}) — {company}\n"
        else:
            line = f"{num}  *{title}* — {company}\n"
            
        job_type = job.get("job_type", "full-time")
        duration = job.get("duration")
        
        subtitle_parts = [f"📍 {location}"]
        if job_type.lower() == "internship":
            if duration:
                subtitle_parts.append(escape_md(f"🎓 Internship ({duration})"))
            else:
                subtitle_parts.append("🎓 Internship")
        elif job_type.lower() != "full-time":
            subtitle_parts.append(escape_md(f"💼 {job_type.title()}"))
            
        if salary:
            subtitle_parts.append(f"💰 {salary}")
            
        subtitle_joined = " \\| ".join(subtitle_parts)
        line += f"     {subtitle_joined}\n"
        if skills_text:
            line += f"     🏷 {skills_text}\n"
        
        if user_skills is not None:
            job_exp = job.get("experience_required")
            details = compute_match_details(user_skills, skills_list, user_exp, job_exp)
            score = details["score"]
            matched_skills = details["matched"]
            missing_skills = details["missing"]
            exp_note = details.get("exp_note")
            
            if plan == "pro":
                if score >= 70:
                    match_text = f"🟢 {score}% match"
                elif score >= 40:
                    match_text = f"🟡 {score}% match"
                else:
                    match_text = f"🔴 {score}% match"
                
                # Show skills ratio
                skill_ratio = f"Skills: {len(matched_skills)}/{len(matched_skills)+len(missing_skills)}"
                line += f"     {match_text} \\| {escape_md(skill_ratio)}\n"
                
                # Skill breakdown
                breakdown = ""
                for s in matched_skills[:4]:
                    breakdown += f"{escape_md(s)} ✅  "
                for s in missing_skills[:3]:
                    breakdown += f"{escape_md(s)} ❌  "
                
                if breakdown:
                    line += f"     {breakdown.strip()}\n"
                
                # Experience note
                if exp_note:
                    line += f"     {escape_md(exp_note)}\n"
                    
            elif plan == "free":
                if score >= 70:
                    line += "     🟢 High match  🔒\n"
                    line += "     \\[Upgrade to see breakdown\\]\n"
                elif score >= 40:
                    line += "     🟡 Partial match  🔒\n"
                    line += "     \\[See which skills you're missing → Pro\\]\n"
                else:
                    line += "     🔴 Low match  🔒\n"
                    line += "     \\[See what you're missing → Pro\\]\n"

        if posted:
            line += f"     {escape_md(posted)}\n"
        line += "\n"
        lines.append(line)

    footer = "━━━━━━━━━━━━━━━━━━━━\n"
    if plan == "free":
        footer += escape_md(f"Showing {showing} of {total_count} (Free plan)")

    return header + "".join(lines) + footer


def job_detail_message(job: dict, plan: str = "free", user_skills: list[str] = None, user_exp: str = "0") -> str:
    """Format single job detail view."""
    title = escape_md(job.get("title", "Untitled"))
    company = escape_md(job.get("company", "Unknown"))
    location = escape_md(job.get("location", "Remote") or "Remote")
    salary = escape_md(job.get("salary", "")) if job.get("salary") else "Not specified"
    job_type = job.get("job_type", "full-time")
    duration = job.get("duration")
    
    subtitle_parts = [f"📍 {location}"]
    if job_type.lower() == "internship":
        if duration:
            subtitle_parts.append(escape_md(f"🎓 Internship ({duration})"))
        else:
            subtitle_parts.append("🎓 Internship")
    elif job_type.lower() != "full-time":
        subtitle_parts.append(escape_md(f"💼 {job_type.title()}"))
        
    if job.get("salary"):
        subtitle_parts.append(f"💰 {salary}")
    else:
        subtitle_parts.append("💰 Not specified")
        
    subtitle_str = " \\| ".join(subtitle_parts)
    url = job.get("url", "")
    portal = job.get("portal_type", "other")
    exp_req = job.get("experience_required")
    skills_list = job.get("skills", [])
    skills_text = escape_md(", ".join(s.title() for s in skills_list)) if skills_list else "None listed"

    match_section = ""
    if user_skills is not None:
        details = compute_match_details(user_skills, skills_list, user_exp, exp_req)
        score = details["score"]
        matched_skills = details["matched"]
        missing_skills = details["missing"]
        exp_note = details.get("exp_note")

        if plan == "pro":
            # Score badge
            if score >= 70:
                badge = f"🟢 *{score}% Match*"
            elif score >= 40:
                badge = f"🟡 *{score}% Match*"
            else:
                badge = f"🔴 *{score}% Match*"
            
            match_section += f"\n{badge}\n"
            match_section += f"Skills: {len(matched_skills)}/{len(matched_skills)+len(missing_skills)} matched\n"
            
            if matched_skills:
                m_text = ", ".join(s for s in matched_skills[:6])
                match_section += f"✅ *Have:* {escape_md(m_text)}\n"
            if missing_skills:
                ms_text = ", ".join(s for s in missing_skills[:5])
                match_section += f"❌ *Missing:* {escape_md(ms_text)}\n"
            if exp_note:
                match_section += f"📅 {escape_md(exp_note)}\n"
            match_section += "\n"
        else:
            # Free user teaser
            if score >= 70:
                match_section = (
                    "\n👆 *You're a strong match for this one\\.*\n"
                    "Upgrade to see your full skill breakdown\\.\n\n"
                )
            elif score < 40:
                match_section = (
                    "\n⚠️ *You might be underqualified for this one\\.*\n"
                    "Upgrade to see which skills you're missing\\.\n\n"
                )

    # Experience requirement line
    exp_line = ""
    if exp_req is not None:
        exp_line = f"📅 Experience: {exp_req}\\+ years required\n"

    return (
        f"*{title} \\- {company}*\n"
        f"{subtitle_str}\n"
        f"🏷 {skills_text}\n"
        f"{exp_line}"
        f"{match_section}"
        f"*Job link:* {escape_md(url)}\n\n"
        "What would you like to do?"
    )


def no_jobs_found() -> str:
    return (
        "😔 *No matching jobs found today*\n\n"
        "Try updating your skills or location in ⚙️ Settings\\.\n"
        "I'll keep searching and notify you when new jobs match\\!"
    )


# ──────────────────────────────────────────────
# Cover Letter
# ──────────────────────────────────────────────

def generating_cover_letter(mode_display: str) -> str:
    return f"⏳ Generating your cover letter\\.\\.\\.\n\n{escape_md(mode_display)}\n\\(This takes a few seconds\\)"


def cover_letter_result(job_title: str, company: str, letter: str) -> str:
    title = escape_md(f"{job_title} — {company}")
    body = letter.replace("\\", "\\\\").replace("`", "\\`")
    return (
        f"✅ *Your Cover Letter — {title}*\n\n"
        f"```text\n{body}\n```\n\n"
        "👆 *Tap the box above to instantly copy it\\!*"
    )


def cover_letter_limit_hit(used: int, max_cl: int, reset_date: str) -> str:
    return (
        f"⚠️ You've used your {used} free cover letters this month\\.\n\n"
        f"Upgrade to Pro \\(₹299/mo\\) for *unlimited* cover letters \\+ 20 jobs/day alerts\\.\n\n"
        f"Your plan resets on {escape_md(reset_date)}\\."
    )


def no_resume_error() -> str:
    return (
        "📄 Please upload your resume first with /resume\\. "
        "I need it to write a personalised cover letter\\."
    )


def quality_mode_upgrade() -> str:
    return (
        "✨ Quality mode uses Llama 3 70B for richer writing\\.\n"
        "Available on *Pro\\+* \\(₹699/mo\\) and *Premium*\\."
    )


# ──────────────────────────────────────────────
# Auto-Apply
# ──────────────────────────────────────────────




# ──────────────────────────────────────────────
# Resume
# ──────────────────────────────────────────────

def resume_status(filename: str | None, uploaded: bool) -> str:
    if uploaded and filename:
        return (
            f"📄 *Your Resume*\n\n"
            f"Status: ✅ Uploaded \\({escape_md(filename)}\\)\n\n"
            "What would you like to do?"
        )
    return (
        "📄 *Resume*\n\n"
        "You haven't uploaded your resume yet\\.\n\n"
        "Upload it once — I'll use it for every cover letter "
        "and auto\\-apply automatically\\.\n\n"
        "Send me your resume as a PDF file \\(max 5MB\\)\\."
    )


def resume_uploaded_success(filename: str) -> str:
    return f"✅ Resume uploaded successfully\\! \\({escape_md(filename)}\\)"


# ──────────────────────────────────────────────
# ATS Analyzer
# ──────────────────────────────────────────────

def ats_result(result: dict) -> str:
    score = result["score"]
    bar = "\U0001f7e9" * (score // 10) + "\u2b1c" * (10 - score // 10)

    # Safely escape each keyword individually before joining
    def safe_list(items: list) -> str:
        return escape_md(", ".join(str(i) for i in items))

    matching = safe_list(result.get("matching_keywords", [])[:8])
    missing = safe_list(result.get("missing_keywords", [])[:8])
    tech_found = safe_list(result.get("tech_match", {}).get("found", [])[:6])
    tech_missing = safe_list(result.get("tech_match", {}).get("missing", [])[:6])

    # Escape each suggestion line independently
    suggestions = "\n".join(
        f"• {escape_md(str(s))}" for s in result.get("suggestions", [])
    )

    matching_line = f"✅ *Matching:* {matching}" if matching else "✅ *Matching:* None"
    missing_line = f"❌ *Missing:* {missing}" if missing else "❌ *Missing:* None"
    tech_found_line = f"🔧 *Tech Found:* {tech_found}" if tech_found else "🔧 *Tech Found:* None"
    tech_missing_line = f"⚠️ *Tech Missing:* {tech_missing}" if tech_missing else ""

    msg = (
        f"📊 *ATS Match Score: {score}%*\n"
        f"{bar}\n\n"
        f"{matching_line}\n"
        f"{missing_line}\n\n"
        f"{tech_found_line}\n"
    )
    if tech_missing_line:
        msg += f"{tech_missing_line}\n"
    if suggestions:
        msg += f"\n💡 *Suggestions:*\n{suggestions}"
    return msg


# ──────────────────────────────────────────────
# Upgrade
# ──────────────────────────────────────────────

def upgrade_plans(current_plan: str) -> str:
    return (
        "💎 *Upgrade to Pro — ₹99/month*\n\n"
        "Here's what you unlock:\n\n"
        "```text\n"
        "             Free     Pro\n"
        "Jobs/day      5      Unlimited\n"
        "Cover letters 1/day   10/day\n"
        "Match score   ❌        ✅\n"
        "App tracker   10 max  Unlimited  \n"
        "Reminders     ❌        ✅\n"
        "Weekly digest ❌        ✅\n"
        "AI model      Fast     Quality\n"
        "```\n\n"
        "All for less than a cup of chai\\. ☕"
    )


# ──────────────────────────────────────────────
# Settings & Status
# ──────────────────────────────────────────────

def settings_menu() -> str:
    return "⚙️ *Settings*\n\nWhat would you like to change?"


def user_status(user: dict) -> str:
    plan_display = {"free": "🆓 Free", "pro": "⭐ Pro", "proplus": "🚀 Pro+", "premium": "💎 Premium"}
    plan = user.get("plan", "free")
    plan_label = escape_md(plan_display.get(plan, "🆓 Free"))
    skills = escape_md(", ".join(user.get("skills", []))) or "None"
    loc_map = {"remote": "🌏 Remote", "india": "🇮🇳 India", "both": "🌐 Both"}
    location = escape_md(loc_map.get(user.get("location_pref", "remote"), "Remote"))
    alert_time = escape_md(user.get("alert_time", "09:00"))

    # Cover letters — daily limit based on plan
    cl_used = user.get("cover_letters_today", 0)
    if plan in ("proplus", "premium"):
        cl_max = "∞"
        cl_label = f"{cl_used}/{cl_max} today"
    elif plan == "pro":
        cl_max = "10"
        cl_label = f"{cl_used}/{cl_max} today"
    else:
        cl_max = "1"
        cl_label = f"{cl_used}/{cl_max} today"

    # ATS checks — daily limit based on plan
    ats_used = user.get("ats_checks_today", 0) or 0
    if plan in ("proplus", "premium"):
        ats_label = f"{ats_used}/∞ today"
    elif plan == "pro":
        ats_label = f"{ats_used}/5 today"
    else:
        ats_label = f"{ats_used}/1 today"

    resume_status = "✅ Uploaded" if user.get("resume_text") else "❌ Not uploaded"

    return (
        f"📊 *Your Status*\n\n"
        f"*Plan:* {plan_label}\n"
        f"*Skills:* {skills}\n"
        f"*Location:* {location}\n"
        f"*Alert Time:* {alert_time} IST\n"
        f"*Resume:* {resume_status}\n\n"
        f"*Cover Letters:* {escape_md(cl_label)}\n"
        f"*ATS Checks:* {escape_md(ats_label)}"
    )


def confirm_delete() -> str:
    return (
        "⚠️ *Delete Account*\n\n"
        "This will permanently delete:\n"
        "• Your profile and preferences\n"
        "• Saved jobs and application history\n"
        "• Uploaded resume\n\n"
        "*This action cannot be undone\\!*"
    )


def account_deleted() -> str:
    return "✅ Your account and all data have been permanently deleted\\. Goodbye\\! 👋"


# ──────────────────────────────────────────────
# Error Messages
# ──────────────────────────────────────────────

def error_ai_failed() -> str:
    return "❌ Sorry, I couldn't generate your cover letter right now\\. Please try again in a minute\\. \\(/coverletter\\)"


def error_job_not_found() -> str:
    return "❌ This job listing may have been removed\\."


def error_rate_limit() -> str:
    return "⏳ Slow down\\! Please wait 30 seconds before trying again\\."


def error_subscription_expired() -> str:
    return "⚠️ Your plan has expired\\. Renew to continue using premium features\\."


def help_message() -> str:
    return (
        "ℹ️ *ApplixyBot Help*\n\n"
        "*Commands:*\n"
        "/start — Open bot / main menu\n"
        "/menu — Show main menu\n"
        "/jobs — View today's job listings\n"
        "/coverletter — Generate a cover letter\n"
        "/resume — Manage your resume\n"
        "/saved — View saved jobs\n"
        "/settings — Change preferences\n"
        "/upgrade — View subscription plans\n"
        "/status — Your plan \\& usage stats\n"
        "/help — This help message\n"
        "/cancel — Cancel current flow\n"
        "/delete\\_account — Delete all your data"
    )
