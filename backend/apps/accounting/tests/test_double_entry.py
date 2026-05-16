from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounting.services.double_entry_service import (
    DoubleEntryValidator,
)


class DoubleEntryTests(TestCase):

    def test_balanced_entries_pass(self):

        entries = [
            {
                "entry_type": "DEBIT",
                "amount": "100.00",
            },
            {
                "entry_type": "CREDIT",
                "amount": "100.00",
            },
        ]

        result = DoubleEntryValidator.validate(entries)

        self.assertTrue(result)

    def test_unbalanced_entries_fail(self):

        entries = [
            {
                "entry_type": "DEBIT",
                "amount": "100.00",
            },
            {
                "entry_type": "CREDIT",
                "amount": "90.00",
            },
        ]

        with self.assertRaises(ValidationError):
            DoubleEntryValidator.validate(entries)
