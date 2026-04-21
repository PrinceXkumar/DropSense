"""
Rule-based risk detection engine.

Evaluates a Student object against predefined academic, financial, and
demographic conditions and returns a risk assessment dict:
    - risk_score  : int 0-100
    - risk_level  : 'Low' | 'Medium' | 'High'
    - risk_color  : CSS-friendly colour token
    - reasons     : list[str] explaining each fired rule
"""


def calculate_risk(student):
    score = 0
    reasons = []

    # ── 1. Academic Performance (Crucial Factor) ──
    # Low semester grades: If average grade < 10 (out of 20), significant risk
    avg_grade = (
        student.curricular_units_1st_sem_grade
        + student.curricular_units_2nd_sem_grade
    ) / 2

    if avg_grade < 10:
        score += 40
        reasons.append(f"Critical academic performance (Avg Grade: {avg_grade:.1f}/20)")
    elif avg_grade < 12:
        score += 20
        reasons.append(f"Below average academic performance (Avg Grade: {avg_grade:.1f}/20)")

    # ── 2. Financial Standing (Requested Priority) ──
    # Tuition fees not paid
    if not student.tuition_fees_up_to_date:
        score += 30
        reasons.append("Tuition fees are NOT up to date")

    # Debtor status
    if student.debtor:
        score += 25
        reasons.append("Identified as a Debtor")

    # ── 3. Other Predictive Factors ──
    # Low approval rate
    total_enrolled = (
        student.curricular_units_1st_sem_enrolled
        + student.curricular_units_2nd_sem_enrolled
    )
    total_approved = (
        student.curricular_units_1st_sem_approved
        + student.curricular_units_2nd_sem_approved
    )
    if total_enrolled > 0:
        approval_rate = total_approved / total_enrolled
        if approval_rate < 0.5:
            score += 15
            reasons.append(f"Low unit approval rate: {approval_rate:.0%}")

    # Mature student risk
    if student.age_at_enrollment > 30:
        score += 5
        reasons.append(f"Non-traditional student age ({student.age_at_enrollment})")

    # ── Final Risk Logic ──
    score = min(score, 100)

    if score >= 60:
        level = "High"
        color = "red"
    elif score >= 25:
        level = "Medium"
        color = "yellow"
    else:
        level = "Low"
        color = "green"

    if not reasons:
        reasons.append("No immediate risk indicators found")

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_color": color,
        "reasons": reasons,
    }
