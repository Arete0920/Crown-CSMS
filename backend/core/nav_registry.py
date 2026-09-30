# backend/core/nav_registry.py
#
# Single source of truth for Crown sidebar navigation.
# Each NavItem declares the permission code required to see that link.
# /api/v1/nav/ filters this list server-side using user_has_permission().
#
# Ordering here controls sidebar group / item order on the frontend.

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class NavItem:
    group: str
    label: str
    href: str
    permission: Optional[str] = None  # None = always visible (keep minimal)


NAV_ITEMS: List[NavItem] = [
    # ── Operations / Leadership ─────────────────────────────────────────────
    NavItem(group="Operations", label="Administration",    href="/admin",           permission="admin.view"),
    NavItem(group="Operations", label="School Board",      href="/board",           permission="board.view"),
    NavItem(group="Operations", label="Finance",           href="/finance",         permission="finance.view"),
    NavItem(group="Operations", label="Billing",           href="/billing",         permission="billing.view"),
    NavItem(group="Operations", label="Office / HR",       href="/office",          permission="office.view"),
    NavItem(group="Operations", label="IT",                href="/it",              permission="it.view"),
    NavItem(group="Operations", label="Facilities",        href="/facilities",      permission="facilities.view"),
    NavItem(group="Operations", label="Transportation",    href="/transportation",  permission="transportation.view"),

    # ── Enrollment & Revenue ────────────────────────────────────────────────
    NavItem(group="Enrollment & Revenue", label="Admissions",      href="/admissions",    permission="admissions.view"),
    NavItem(group="Enrollment & Revenue", label="Financial Aid",   href="/financial-aid", permission="financial_aid.view"),
    NavItem(group="Enrollment & Revenue", label="Marketing",       href="/marketing",     permission="marketing.view"),
    NavItem(group="Enrollment & Revenue", label="Kingdom Path",    href="/kingdom-path/market-study", permission="marketing.view"),
    NavItem(group="Enrollment & Revenue", label="Survey Intelligence", href="/survey-intelligence", permission="marketing.view"),
    NavItem(group="Enrollment & Revenue", label="Advancement",     href="/advancement",   permission="advancement.view"),

    # ── Academics ──────────────────────────────────────────────────────────
    NavItem(group="Academics", label="Academics",             href="/academics",        permission="academics.view"),
    NavItem(group="Academics", label="Teacher",               href="/teacher",          permission="teacher.view"),
    NavItem(group="Academics", label="Registrar",             href="/registrar",        permission="registrar.view"),
    NavItem(group="Academics", label="Academic Support",      href="/academic-support", permission="academic_support.view"),
    NavItem(group="Academics", label="Library",               href="/library",          permission="library.view"),
    NavItem(group="Academics", label="Extended Care",         href="/extended-care",    permission="extended_care.view"),
    NavItem(group="Academics", label="PD / Staff Dev",        href="/pd",               permission="pd.view"),
    NavItem(group="Academics", label="Communications",        href="/communications-director", permission="communications.view"),

    # ── Student & Family ───────────────────────────────────────────────────
    NavItem(group="Student & Family", label="Parent",              href="/parent",         permission="parent.view"),
    NavItem(group="Student & Family", label="Student",             href="/student",        permission="student.view"),
    NavItem(group="Student & Family", label="Health / Nurse",      href="/health",         permission="health.view"),
    NavItem(group="Student & Family", label="Counseling",          href="/counseling",     permission="counseling.view"),
    NavItem(group="Student & Family", label="Food Services",       href="/food",           permission="food.view"),
    NavItem(group="Student & Family", label="Athletics",           href="/athletics",      permission="athletics.view"),
    NavItem(group="Student & Family", label="Fine Arts",           href="/fine-arts",      permission="fine_arts.view"),
    NavItem(group="Student & Family", label="Spiritual Life",      href="/spiritual-life", permission="spiritual_life.view"),
    NavItem(group="Student & Family", label="Student Services",    href="/student-services", permission="student_services.view"),

    # ── Institutional Operations ──────────────────────────────────────────────
    NavItem(group="Institutional Operations", label="Human Resources", href="/hr",          permission="hr.view"),

    # ── Safety & Integrity ─────────────────────────────────────────────────
    NavItem(group="Safety & Integrity", label="Safety",             href="/safety",      permission="safety.view"),
    NavItem(group="Safety & Integrity", label="Security",           href="/security",    permission="security.view"),
    NavItem(group="Safety & Integrity", label="System Integrity",   href="/integrity",   permission="integrity.view"),
]
