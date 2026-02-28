import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_board_urls_exist():
    # Both /api/ and /api/v1/ are mounted entry points for api_v1_urls.
    # Reverse resolves to /api/ prefix; both prefixes route to the same views.
    assert reverse("board_oversight_metrics").endswith("/board/metrics/")
    assert reverse("board_oversight_dashboard").endswith("/board/dashboard/")
    assert reverse("board_oversight_snapshots").endswith("/board/snapshots/")
    assert reverse("board_oversight_packets").endswith("/board/packets/")
