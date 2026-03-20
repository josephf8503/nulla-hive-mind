from __future__ import annotations

from core.public_landing_page import render_public_landing_page_html


def test_public_landing_page_explains_the_one_lane_story() -> None:
    html = render_public_landing_page_html()

    assert "NULLA · Local-first agent runtime" in html
    assert "Your agent. On your machine first." in html
    assert "One system. One lane." in html
    assert "One system. Many doors." in html
    assert "Local runtime" in html
    assert "Outside help, when asked" in html
    assert "Get NULLA" in html
    assert 'href="/feed"' in html
    assert 'href="/hive"' in html
    assert "Still unfinished" in html
