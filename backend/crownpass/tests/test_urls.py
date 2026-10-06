from django.core.checks import Tags, run_checks


def test_crownpass_dual_mount_has_no_duplicate_namespace_warning():
    messages = run_checks(tags=[Tags.urls])
    crownpass_namespace_warnings = [
        message
        for message in messages
        if message.id == "urls.W005" and "crownpass" in str(message.msg).lower()
    ]
    assert crownpass_namespace_warnings == []
