ACCOUNTING_EVENT_SCHEMA = {
    "event_id": "uuid",
    "tenant_id": "uuid",
    "correlation_id": "uuid",
    "source_system": "string",
    "event_type": "string",
    "timestamp": "datetime",
    "initiated_by": "uuid",
    "currency": "string",
    "entries": [
        {
            "account_code": "string",
            "entry_type": "DEBIT|CREDIT",
            "amount": "decimal",
        }
    ]
}
