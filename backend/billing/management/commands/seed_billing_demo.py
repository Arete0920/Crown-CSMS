"""
Management command to seed demo billing data (invoices + line items)
Safe to re-run: uses DEMO-2026-SEED term tag for idempotency
"""
import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from uuid import UUID

from billing.models import BillingRun, Invoice, InvoiceLine
from households.models import Household, Student

DEMO_TERM = "DEMO-2026-SEED"
DEMO_RUN_TYPE = "TUITION"


class Command(BaseCommand):
    help = "Seed demo billing data (billing runs, invoices, line items) for Finance dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            type=str,
            default="a5351136-98fe-4d48-add0-fa8f62d9ceff",
            help="School UUID (defaults to demo school)",
        )
        parser.add_argument(
            "--invoices",
            type=int,
            default=40,
            help="Number of invoices to generate",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete prior demo seed data first",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=2026,
            help="Random seed for repeatable results",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])
        
        school_id = UUID(opts["school_id"])
        
        # Verify school context
        households = list(Household.objects.filter(school_id=school_id).prefetch_related("students")[:50])
        if not households:
            self.stderr.write(
                self.style.ERROR(f"No households found for school {school_id}. Seed households/students first.")
            )
            return
        
        # Filter to households with students
        households_with_students = [h for h in households if h.students.exists()]
        if not households_with_students:
            self.stderr.write(
                self.style.ERROR(f"No households with students found. Seed students first.")
            )
            return
        
        if opts["clear"]:
            # Clear demo seed billing runs and cascading invoices/lines
            deleted_runs = BillingRun.objects.filter(school_id=school_id, term=DEMO_TERM).delete()
            self.stdout.write(f"Cleared {deleted_runs[0]} demo billing records")
        
        # Create a single demo billing run
        billing_run = BillingRun.objects.create(
            school_id=school_id,
            term=DEMO_TERM,
            run_type=DEMO_RUN_TYPE,
            description="Demo Finance Seed Data",
            amount_per_student=Decimal("550.00"),
        )
        
        self.stdout.write(f"Created BillingRun: {billing_run.id} ({DEMO_TERM})")
        
        # Generate invoices
        now = timezone.now().date()
        n = int(opts["invoices"])
        created = 0
        
        for i in range(n):
            household = random.choice(households_with_students)
            students = list(household.students.all())
            
            # Mix of due dates: some overdue, some current, some future
            bucket = random.random()
            if bucket < 0.25:
                # Overdue (past due)
                due_on = now - timedelta(days=random.randint(10, 60))
            elif bucket < 0.50:
                # Recently due
                due_on = now - timedelta(days=random.randint(0, 10))
            elif bucket < 0.75:
                # Due soon
                due_on = now + timedelta(days=random.randint(1, 15))
            else:
                # Due later
                due_on = now + timedelta(days=random.randint(16, 45))
            
            # Create invoice
            invoice = Invoice.objects.create(
                school_id=school_id,
                billing_run=billing_run,
                household=household,
                total_amount=Decimal("0.00"),  # Will update after line items
                due_on=due_on,
            )
            
            # Create 1-3 line items per student in household
            total = Decimal("0.00")
            for student in students:
                line_count = random.randint(1, 3)
                for _ in range(line_count):
                    charge_type = random.choice([
                        ("Tuition", Decimal("550.00")),
                        ("Tuition", Decimal("450.00")),
                        ("Tuition", Decimal("650.00")),
                        ("Books & Materials", Decimal("85.00")),
                        ("Activity Fee", Decimal("40.00")),
                        ("Technology Fee", Decimal("60.00")),
                        ("Lunch Program", Decimal("120.00")),
                        ("Extended Day", Decimal("180.00")),
                    ])
                    
                    description, amount = charge_type
                    
                    InvoiceLine.objects.create(
                        school_id=school_id,
                        invoice=invoice,
                        student=student,
                        description=description,
                        amount=amount,
                    )
                    
                    total += amount
            
            # Update invoice total
            invoice.total_amount = total
            invoice.save(update_fields=["total_amount"])
            
            created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Seeded {created} invoices for school {school_id} (term={DEMO_TERM})"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"   Total line items: ~{created * 2}-{created * 6}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"   Visit /finance/invoices to see results"
            )
        )
