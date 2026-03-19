from __future__ import annotations

from core.public_landing_page import render_public_landing_page_html


def test_public_landing_page_explains_the_one_lane_story() -> None:
    html = render_public_landing_page_html()

    assert "Your AI. On your machine first." in html
    assert "One system. One lane." in html
    assert "Local NULLA agent" in html
    assert "Optional trusted helpers" in html
    assert "Get NULLA" in html
    assert 'href="/feed"' in html
    assert 'href="/hive"' in html
    assert "Not pretending yet" in html
