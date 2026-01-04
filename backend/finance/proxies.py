from core.models import LedgerEntry, TuitionPlan, StudentTuition


class FinanceLedgerEntry(LedgerEntry):
    class Meta:
        proxy = True
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"
        app_label = "finance"


class FinanceTuitionPlan(TuitionPlan):
    class Meta:
        proxy = True
        verbose_name = "Tuition Plan"
        verbose_name_plural = "Tuition Plans"
        app_label = "finance"


class FinanceStudentTuition(StudentTuition):
    class Meta:
        proxy = True
        verbose_name = "Student Tuition"
        verbose_name_plural = "Student Tuitions"
        app_label = "finance"
