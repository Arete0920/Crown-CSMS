def health_check():
    return {"status": "connector ready", "version": "1.0.0"}


def get_connector_status():
    """
    Returns status of all integration connectors.
    In MVP: all report ready unless explicitly toggled off via env.
    """
    import os
    connectors = {
        "sis": os.getenv("CONNECTOR_SIS_ENABLED", "true").lower() == "true",
        "lms": os.getenv("CONNECTOR_LMS_ENABLED", "false").lower() == "true",
        "erp": os.getenv("CONNECTOR_ERP_ENABLED", "false").lower() == "true",
        "payment": os.getenv("CONNECTOR_PAYMENT_ENABLED", "false").lower() == "true",
    }
    return {
        "connectors": [
            {"name": name, "enabled": enabled, "status": "ready" if enabled else "disabled"}
            for name, enabled in connectors.items()
        ]
    }
