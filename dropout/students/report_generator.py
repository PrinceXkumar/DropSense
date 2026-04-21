from io import BytesIO
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_risk_report_pdf(student, risk_data, ml_data, contributions):
    """
    Generates a PDF Risk Report using ReportLab based on student data, risk engine data, and ML predictor data.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=50,
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1e1e2f"),
        spaceAfter=15,
        alignment=1, # Center
    )
    
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.gray,
        spaceAfter=30,
        alignment=1, # Center
    )
    
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=colors.HexColor("#2d3748"),
        spaceAfter=10,
        spaceBefore=20,
    )
    
    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#4a5568"),
        spaceAfter=8,
    )
    
    danger_style = ParagraphStyle(
        "DangerText",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#e53e3e"),
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    
    success_style = ParagraphStyle(
        "SuccessText",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#38a169"),
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    
    warning_style = ParagraphStyle(
        "WarningText",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#d69e2e"),
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )

    story = []
    
    # --- Header ---
    story.append(Paragraph("Student Risk & Action Report", title_style))
    story.append(Paragraph(f"Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=20))
    
    # --- Student Info ---
    story.append(Paragraph(f"<b>Student Profile: #{student.pk}</b>", heading_style))
    story.append(Paragraph(f"<b>Course:</b> {student.course}", normal_style))
    story.append(Paragraph(f"<b>Age at Enrollment:</b> {student.age_at_enrollment}", normal_style))
    story.append(Paragraph(f"<b>Gender:</b> {student.gender}", normal_style))
    if student.target:
        story.append(Paragraph(f"<b>Current System Status:</b> {student.target}", normal_style))
    
    story.append(Spacer(1, 10))
    
    # --- Risk Assessment Summary ---
    story.append(Paragraph("<b>1. Rule-Based Risk Assessment</b>", heading_style))
    
    risk_level = risk_data.get("risk_level", "Low")
    risk_score = risk_data.get("risk_score", 0)
    
    if risk_level == "High":
        styled_level = Paragraph(f"🚨 <b>Risk Level: {risk_level} ({risk_score}%)</b>", danger_style)
    elif risk_level == "Medium":
        styled_level = Paragraph(f"⚠️ <b>Risk Level: {risk_level} ({risk_score}%)</b>", warning_style)
    else:
        styled_level = Paragraph(f"✅ <b>Risk Level: {risk_level} ({risk_score}%)</b>", success_style)
        
    story.append(styled_level)
    
    reasons = risk_data.get("reasons", [])
    if reasons:
        story.append(Paragraph("<b>Flagged Risk Factors:</b>", normal_style))
        for r in reasons:
            story.append(Paragraph(f"• {r}", normal_style))
    else:
        story.append(Paragraph("No significant risk factors flagged by rule engine.", normal_style))

    story.append(Spacer(1, 15))

    # --- Machine Learning Prediction ---
    story.append(Paragraph("<b>2. AI / Machine Learning Prediction</b>", heading_style))
    if ml_data and ml_data.get("model_available"):
        ml_prediction = ml_data.get("prediction", "Unknown")
        ml_confidence = ml_data.get("confidence", 0)
        
        ml_color = success_style
        if ml_prediction == "Dropout":
            ml_color = danger_style
        elif ml_prediction == "Enrolled":
            ml_color = warning_style
            
        story.append(Paragraph(f"<b>Predicted Outcome:</b> {ml_prediction}", ml_color))
        story.append(Paragraph(f"<b>Model Confidence:</b> {ml_confidence}%", normal_style))
        
        # Probabilities Table
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>Class Probabilities:</b>", normal_style))
        
        prob_data = [["Outcome", "Probability (%)"]]
        for cls, prob in ml_data.get("probabilities", {}).items():
            prob_data.append([cls, f"{prob}%"])
            
        prob_table = Table(prob_data, colWidths=[150, 150])
        prob_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ]))
        story.append(prob_table)
        story.append(Spacer(1, 15))
        
        if contributions:
            story.append(Paragraph("<b>Top Feature Drivers (Specific to this Student):</b>", normal_style))
            cont_data = [["Feature", "Influence (%)", "Value"]]
            for cont in contributions:
                # Use .get() to avoid KeyError if keys change in future
                feature_name = cont.get("feature", "Unknown")
                importance = cont.get("importance", 0)
                val = cont.get("value", "N/A")
                cont_data.append([feature_name, f"{importance}%", str(val)])
                
            cont_table = Table(cont_data, colWidths=[200, 100, 100])
            cont_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ]))
            story.append(cont_table)
    else:
        story.append(Paragraph("<i>Machine Learning model predictions are currently unavailable.</i>", normal_style))

    # --- Academic Overview ---
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>3. Academic Overview</b>", heading_style))
    academic_data = [
        ["Metric", "Semester 1", "Semester 2"],
        ["Enrolled Units", str(student.curricular_units_1st_sem_enrolled), str(student.curricular_units_2nd_sem_enrolled)],
        ["Approved Units", str(student.curricular_units_1st_sem_approved), str(student.curricular_units_2nd_sem_approved)],
        ["Average Grade", str(student.curricular_units_1st_sem_grade), str(student.curricular_units_2nd_sem_grade)],
    ]
    acad_table = Table(academic_data, colWidths=[150, 100, 100])
    acad_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
    ]))
    story.append(acad_table)
    
    # --- Action Recommendations ---
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>4. Action Plan / Recommendations</b>", heading_style))
    if risk_level == "High":
        story.append(Paragraph("• Immediate mentor intervention recommended — schedule a one-on-one meeting within 48 hours.", normal_style))
        story.append(Paragraph("• Notify parent/guardian about the student's academic and financial status immediately.", normal_style))
        story.append(Paragraph("• Create an academic improvement plan with measurable targets.", normal_style))
    elif risk_level == "Medium":
        story.append(Paragraph("• Monitor student progress closely over the next semester with bi-weekly check-ins.", normal_style))
        story.append(Paragraph("• Recommend academic support resources such as tutoring or study groups.", normal_style))
    else:
        story.append(Paragraph("• Student appears to be on track. No immediate intervention required.", normal_style))

    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
