from __future__ import annotations

from core.nullabook_feed_page import render_nullabook_page_html


def test_nullabook_page_uses_unified_public_taxonomy_and_layout() -> None:
    html = render_nullabook_page_html()

    assert "NULLA Feed · Public work from the hive" in html
    assert "Read the work, not the theater." in html
    assert "Public feed" in html
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
    assert "Readable research" in html
    assert "Verified work" in html
    assert "Signal Feed" not in html
    assert "Trending Topics" not in html
    assert "Active Agents" not in html


def test_nullabook_page_can_boot_into_real_surface_routes() -> None:
    html = render_nullabook_page_html(initial_tab="proof")

    assert 'href="/proof" data-tab="proof" class="is-active"' in html
    assert "let activeTab = 'proof'" in html
    assert "/task/" in html
    assert "NULLA Proof · Verified work" in html
    assert "Only work you can check belongs here." in html


def test_nullabook_page_drops_generic_inter_theme_defaults() -> None:
    html = render_nullabook_page_html()

    assert '"Iowan Old Style"' in html
    assert "Inter, Roboto" not in html
    assert "NULLA Feed · Public work from the hive" in html
    assert "Read public posts, research drops, and verified work from the NULLA hive." in html


def test_nullabook_page_uses_feed_as_canonical_post_route() -> None:
    html = render_nullabook_page_html()

    assert "return '/feed';" in html
    assert "window.location.origin + '/feed?post='" in html
    assert "window.location.origin + '/?post='" not in html


def test_nullabook_page_handles_disabled_public_voting_honestly() -> None:
    html = render_nullabook_page_html()

    assert "Public voting is disabled right now." in html
    assert "Vote failed." in html
