#!/usr/bin/env python3
"""Build the newly authored, two-page pilot overview from first-party text.

Run from the repository's locked Python environment. The original October 8
document, including its authenticity records, remains in version history at
b5ccf6102a1bdc786e2348d58d2844d70256a810. This builder creates a new document;
it does not load, modify, or strip metadata from that original.
"""

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent
NAVY = colors.HexColor("#173746")
TEAL = colors.HexColor("#1c6064")
GOLD = colors.HexColor("#d39c49")
CREAM = colors.HexColor("#fcf8f0")
PALE = colors.HexColor("#edf4f4")
STYLES = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=8,
                              leading=11, textColor=TEAL, spaceAfter=12),
    "title": ParagraphStyle("title", fontName="Times-Bold", fontSize=34,
                            leading=38, textColor=NAVY, spaceAfter=9),
    "lead": ParagraphStyle("lead", fontName="Helvetica", fontSize=12,
                           leading=17, textColor=NAVY, spaceAfter=13),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.3,
                           leading=13.5, textColor=NAVY, spaceAfter=8),
    "heading": ParagraphStyle("heading", fontName="Helvetica-Bold", fontSize=10,
                              leading=14, textColor=TEAL, spaceBefore=11, spaceAfter=8),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8,
                            leading=11, textColor=NAVY, spaceAfter=5),
    "step": ParagraphStyle("step", fontName="Helvetica-Bold", fontSize=8.3,
                           leading=15, textColor=NAVY, alignment=TA_CENTER),
}


def p(text, style="body"):
    return Paragraph(text, STYLES[style])


def cards(entries):
    cells = [[p(title, "heading"), p(body)] for title, body in entries]
    table = Table([cells], colWidths=[180] * len(cells))
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BACKGROUND", (1, 0), (1, 0), CREAM),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def section(title, body):
    return KeepTogether([p(title, "heading"), p(body)])


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1)
    canvas.line(36, 38, 576, 38)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(NAVY)
    canvas.drawString(36, 25, "ARETE ADVISORY GROUP  /  JIREH SGO  /  PILOT DEVELOPMENT")
    canvas.drawRightString(576, 25, f"October 18, 2026  |  {document.page} / 2")
    canvas.restoreState()


def build():
    # Reproducible build date for this edition; allow an explicit release epoch.
    os.environ.setdefault("SOURCE_DATE_EPOCH", "1792281600")
    output = ROOT / "resources/jireh-sgo-overview.pdf"
    doc = SimpleDocTemplate(
        str(output), pagesize=letter, leftMargin=36, rightMargin=36,
        topMargin=36, bottomMargin=53, pageCompression=1, invariant=1,
        title="Jireh SGO | Pilot Product Overview", author="Arete Advisory Group",
        subject="Intended scholarship-administration workflows and pilot scope",
        creator="CROWN document build", lang="en-US",
    )
    story = [
        p("ARETE ADVISORY GROUP  /  SCHOLARSHIP SOFTWARE", "eyebrow"),
        p("Introducing Jireh SGO", "title"),
        p("Purposeful scholarship administration.<br/>Clear decisions. Accountable stewardship.", "lead"),
        p("A standalone scholarship-administration platform designed to bring greater clarity to "
          "applications, household financial assessment, grantor decisions, school coordination, "
          "and scholarship accountability."),
        section("SEEKING DESIGN PARTNERS AND PILOT ORGANIZATIONS",
                "Jireh SGO is in development. Arete is inviting experienced scholarship-granting "
                "organizations to help shape operational requirements and pilot priorities."),
        cards([
            ("LESS ADMINISTRATIVE WORK", "Reduce repeated manual exchange among families, scholarship teams, and schools."),
            ("INFORMED DECISIONS", "Separate eligibility, financial need, human review, and final award authority."),
            ("CLEAR ACCOUNTABILITY", "Track commitments, required evidence, participating schools, and future settlement records."),
        ]),
        p("THE PRODUCT VISION", "heading"),
        p("<b>Application and renewal workflows.</b> A family-facing process with program-specific questions, "
          "document intake, status updates, and annual renewal support."),
        p("<b>Configurable financial analysis.</b> SGO-approved need methodologies that distinguish household "
          "capacity from legal eligibility and allow documented hardship decisions."),
        p("<b>Grantor-governed awards.</b> Role-based reviews, policy versions, human authorization, "
          "award commitments, and an auditable record of decisions."),
        p("<b>Participating-school connections.</b> Enrollment and eligible-charge verification, award "
          "notices, and planned secure data exchange with CROWN and other school systems."),
        p("<b>Financial controls and reporting.</b> Distinguish award commitments, verified funds, tuition "
          "allocations, reversals, and SGO reporting obligations."),
        p("ONE INTENDED WORKFLOW", "heading"),
    ]
    workflow = Table([[p(f"{i:02d}<br/>{name}", "step") for i, name in enumerate(
        ("APPLY", "VERIFY", "REVIEW", "COMMIT", "RECONCILE"), 1)]], colWidths=[108] * 5)
    workflow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [workflow, Spacer(1, 12),
              p("Designed for scholarship-granting organizations and independent K-12 scholarship funds."),
              p("<b>Discuss a pilot:</b> AreteAdvisoryGroup.com/contact  |  (302) 373-2168"),
              PageBreak(),
              p("JIREH SGO  /  ROLES AND RESPONSIBILITIES", "eyebrow"),
              p("One connected workflow.", "title"),
              p("Distinct responsibilities at every step.", "lead"),
              p("Jireh SGO is being built to support authorized coordination. The SGO and participating "
                "schools retain their own legal, financial, and operational responsibilities."),
              cards([
                  ("THE SGO", "Sets program policy, verifies eligibility, approves awards, controls scholarship "
                   "funds, and owns its regulatory filings."),
                  ("THE SCHOOL", "Confirms enrollment and eligible charges, receives authorized funds, and "
                   "maintains accurate family accounts."),
                  ("JIREH SGO", "Is designed to coordinate secure application data, reviews, evidence references, "
                   "award commitments, and financial records."),
              ]), p("PLANNED ADMINISTRATIVE LIFECYCLE", "heading")]
    for title, body in [
        ("01 Apply", "A family submits the program-specific application and authorized financial information."),
        ("02 Verify", "The SGO obtains acceptable evidence and determines which verification rules apply."),
        ("03 Decide", "Authorized grantor reviewers assess eligibility, need, priorities, and the proposed award."),
        ("04 Coordinate", "Participating schools confirm enrollment, tuition, and eligible educational charges."),
        ("05 Fund", "The SGO authorizes and remits payments through its approved financial provider."),
        ("06 Reconcile", "Grantor and school compare cleared payments, eligible allocations, exceptions, and reports."),
    ]:
        story.append(p(f"<b>{title}.</b> {body}"))
    story += [
        section("PILOT SCOPE AND OPERATIONAL ACCEPTANCE",
                "Pilot planning covers organization records, roles, program definitions, applications, "
                "reviewer attestations, award commitments, and audit events. Production use requires separate "
                "verification of the standalone portal, financial assessments, integrations, fund administration, "
                "disbursement, reconciliation, reporting, and operational security."),
        section("PROGRAM-SPECIFIC REQUIREMENTS",
                "The grantor must confirm applicable eligibility, qualification, participation, and operating "
                "requirements with its qualified advisers. Jireh SGO does not confer grantor status or "
                "federal or state compliance certification."),
        section("BECOME A DESIGN OR PILOT PARTNER",
                "Share your application volumes, assessment methods, renewal needs, donor stewardship, "
                "audit demands, school interfaces, and greatest administrative bottlenecks."),
        p("<b>AreteAdvisoryGroup.com/contact</b>  |  (302) 373-2168<br/>jmegahan@areteadvisorygroup.com"),
        p("<b>PRODUCT STATUS: PILOT DEVELOPMENT.</b> This overview describes the intended product. "
          "It does not represent a production release, live SGO funding, verified third-party integrations, "
          "eligibility determination, or federal/state compliance certification.", "small"),
    ]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    build()
