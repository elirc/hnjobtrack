def compute_match_score(job: dict, prefs: dict) -> float:
    """
    Compute a 0-100 match score between a job and user preferences.

    Scoring breakdown:
    - Skill overlap: 40 points max
    - Role match: 20 points max
    - Location match: 15 points max
    - Remote match: 10 points max
    - Salary fit: 10 points max
    - Visa match: 5 points max
    """
    score = 0.0

    # Skill overlap (40 pts)
    user_skills = set(s.lower() for s in (prefs.get("skills") or []))
    job_skills = set(s.lower() for s in (job.get("skills") or []))
    if user_skills and job_skills:
        overlap = len(user_skills & job_skills)
        max_possible = min(len(user_skills), len(job_skills))
        if max_possible > 0:
            score += (overlap / max_possible) * 40

    # Role match (20 pts)
    user_roles = [r.lower() for r in (prefs.get("roles") or [])]
    job_role = (job.get("role") or "").lower()
    if user_roles and job_role:
        for role in user_roles:
            if role in job_role or job_role in role:
                score += 20
                break
            words = role.split()
            matching_words = sum(1 for w in words if w in job_role)
            if matching_words >= len(words) * 0.5:
                score += 10
                break

    # Location match (15 pts)
    user_locations = [loc.lower() for loc in (prefs.get("locations") or [])]
    job_locations = [loc.lower() for loc in (job.get("location") or [])]
    if user_locations and job_locations:
        for ul in user_locations:
            for jl in job_locations:
                if ul in jl or jl in ul:
                    score += 15
                    break
            else:
                continue
            break

    # Remote match (10 pts)
    if prefs.get("remote_only") and job.get("remote") in ("yes", "hybrid"):
        score += 10
    elif not prefs.get("remote_only"):
        score += 5

    # Salary fit (10 pts)
    user_salary_min = prefs.get("salary_min")
    job_salary_max = job.get("salary_max")
    job_salary_min = job.get("salary_min")
    if user_salary_min and job_salary_max:
        if job_salary_max >= user_salary_min:
            score += 10
        elif job_salary_min and job_salary_min >= user_salary_min * 0.8:
            score += 5

    # Visa (5 pts)
    if prefs.get("visa_sponsorship"):
        if job.get("visa_sponsorship"):
            score += 5
    else:
        score += 5

    # Exclude companies
    excluded = [c.lower() for c in (prefs.get("excluded_companies") or [])]
    company = (job.get("company") or "").lower()
    if company and company in excluded:
        score = 0

    return round(min(score, 100), 1)


def get_match_breakdown(job: dict, prefs: dict) -> dict:
    """Return a breakdown of how the match score was computed."""
    breakdown = {}

    user_skills = set(s.lower() for s in (prefs.get("skills") or []))
    job_skills = set(s.lower() for s in (job.get("skills") or []))
    matched_skills = list(user_skills & job_skills) if user_skills and job_skills else []
    breakdown["matched_skills"] = matched_skills
    breakdown["skill_score"] = len(matched_skills)

    user_roles = [r.lower() for r in (prefs.get("roles") or [])]
    job_role = (job.get("role") or "").lower()
    breakdown["role_match"] = any(
        r in job_role or job_role in r for r in user_roles
    ) if user_roles and job_role else False

    breakdown["location_match"] = False
    user_locations = [loc.lower() for loc in (prefs.get("locations") or [])]
    job_locations = [loc.lower() for loc in (job.get("location") or [])]
    for ul in user_locations:
        for jl in job_locations:
            if ul in jl or jl in ul:
                breakdown["location_match"] = True

    breakdown["remote_match"] = bool(
        prefs.get("remote_only") and job.get("remote") in ("yes", "hybrid")
    )
    breakdown["salary_fit"] = bool(
        prefs.get("salary_min")
        and job.get("salary_max")
        and job["salary_max"] >= prefs["salary_min"]
    )
    breakdown["total_score"] = compute_match_score(job, prefs)

    return breakdown
