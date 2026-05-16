from decimal import Decimal

from django.core.exceptions import ValidationError


class DoubleEntryValidator:

    @staticmethod
    def validate(entries):

        debit_total = Decimal("0.00")
        credit_total = Decimal("0.00")

        for entry in entries:

            amount = Decimal(entry["amount"])

            if amount <= 0:
                raise ValidationError(
                    "Entry amount must be positive."
                )

            if entry["entry_type"] == "DEBIT":
                debit_total += amount

            elif entry["entry_type"] == "CREDIT":
                credit_total += amount

            else:
                raise ValidationError(
                    "Invalid entry type."
                )

        if debit_total != credit_total:
            raise ValidationError(
                "Debits and credits are not balanced."
            )

        return True
