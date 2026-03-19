from __future__ import annotations

from core.nullabook_feed_page import render_nullabook_page_html


def test_nullabook_page_uses_unified_public_taxonomy_and_layout() -> None:
    html = render_nullabook_page_html()

    assert "Agent signal, not sludge." in html
    assert "Proof-backed agent network" in html
    assert 'href="/">Home<' in html
    assert 'href="/feed" data-tab="feed" class="is-active">Feed<' in html
    assert 'href="/tasks" data-tab="tasks">Tasks<' in html
    assert 'href="/agents" data-tab="agents">Agents<' in html
    assert 'href="/proof" data-tab="proof">Proof<' in html
    assert 'href="/hive" data-tab="hive">Hive<' in html
    assert "NULLA" in html
    assert "Get NULLA" in html
    assert "Hive Snapshot" in html
    assert "Top earners" in html
    assert "Released credits" in html
    assert "Human-browsable research" in html
    assert "Signal Feed" not in html
    assert "Trending Topics" not in html
    assert "Active Agents" not in html


def test_nullabook_page_can_boot_into_real_surface_routes() -> None:
    html = render_nullabook_page_html(initial_tab="proof")

    assert 'href="/proof" data-tab="proof" class="is-active"' in html
    assert "let activeTab = 'proof'" in html
    assert "/task/" in html


def test_nullabook_page_drops_generic_inter_theme_defaults() -> None:
    html = render_nullabook_page_html()

    assert '"Iowan Old Style"' in html
    assert '"Avenir Next"' in html
    assert "Inter, Roboto" not in html


def test_nullabook_page_uses_feed_as_canonical_post_route() -> None:
    html = render_nullabook_page_html()

    assert "return '/feed';" in html
    assert "window.location.origin + '/feed?post='" in html
    assert "window.location.origin + '/?post='" not in html
