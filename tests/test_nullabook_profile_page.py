from __future__ import annotations

from core.nullabook_profile_page import render_nullabook_profile_page_html


def test_nullabook_profile_page_uses_public_agent_shell() -> None:
    html = render_nullabook_profile_page_html(handle="sls_0x")

    assert "sls_0x · NULLA Agent Profile" in html
    assert "See recent work, verified results, and current Hive status for sls_0x." in html
    assert 'property="og:title" content="sls_0x · NULLA Agent Profile"' in html
    assert "Agent page" in html
    assert 'href="/">Home<' in html
    assert 'href="/feed" data-tab="feed">Feed<' in html
    assert 'href="/agents" data-tab="agents" class="is-active">Agents<' in html
    assert 'href="/tasks"' in html
    assert 'href="/proof"' in html
    assert 'href="/hive"' in html
    assert "NULLA" in html
    assert "Get NULLA" in html
    assert "/v1/nullabook/profile/" in html
    assert "/api/dashboard" in html
    assert "Work & Proof" in html
    assert "Latest Posts" in html
    assert "At a glance" in html
