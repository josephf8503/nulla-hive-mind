from __future__ import annotations

import ssl
from collections.abc import Callable
from http.server import ThreadingHTTPServer

from core.nulla_workstation_ui import NULLA_WORKSTATION_DEPLOYMENT_VERSION
from core.web.watch.config import BrainHiveWatchServerConfig
from core.web.watch.fetchers import (
    fetch_dashboard_from_upstreams as _core_fetch_dashboard_from_upstreams,
)
from core.web.watch.fetchers import (
    fetch_topic_from_upstreams as _core_fetch_topic_from_upstreams,
)
from core.web.watch.fetchers import (
    fetch_topic_posts_from_upstreams as _core_fetch_topic_posts_from_upstreams,
)
from core.web.watch.fetchers import (
    http_get_json as _core_http_get_json,
)
from core.web.watch.fetchers import (
    proxy_nullabook_get as _core_proxy_nullabook_get,
)
from core.web.watch.server import build_watch_server
from core.web.watch.tls import (
    build_tls_context as _core_build_tls_context,
)
from core.web.watch.tls import (
    normalize_base_url as _core_normalize_base_url,
)
from core.web.watch.tls import (
    requires_public_tls as _core_requires_public_tls,
)
from core.web.watch.tls import (
    ssl_context_for_url as _core_ssl_context_for_url,
)
from core.web.watch.tls import (
    validate_tls_config as _core_validate_tls_config,
)
from core.web.watch.tls import (
    watch_tls_enabled as _core_watch_tls_enabled,
)


def _http_get_json(
    url: str,
    *,
    timeout_seconds: int,
    auth_token: str | None = None,
    tls_ca_file: str | None = None,
    tls_insecure_skip_verify: bool = False,
) -> dict:
    return _core_http_get_json(
        url,
        timeout_seconds=timeout_seconds,
        auth_token=auth_token,
        tls_ca_file=tls_ca_file,
        tls_insecure_skip_verify=tls_insecure_skip_verify,
        ssl_context_for_url_func=_ssl_context_for_url,
    )


def _proxy_nullabook_get(
    upstream_base_urls: tuple[str, ...],
    path: str,
    *,
    timeout_seconds: int = 5,
    auth_token: str | None = None,
    auth_tokens_by_base_url: dict[str, str] | None = None,
    tls_ca_file: str | None = None,
    tls_insecure_skip_verify: bool = False,
) -> dict:
    return _core_proxy_nullabook_get(
        upstream_base_urls,
        path,
        timeout_seconds=timeout_seconds,
        auth_token=auth_token,
        auth_tokens_by_base_url=auth_tokens_by_base_url,
        tls_ca_file=tls_ca_file,
        tls_insecure_skip_verify=tls_insecure_skip_verify,
        fetch_json=_http_get_json,
        normalize_base_url_func=_normalize_base_url,
    )


def fetch_dashboard_from_upstreams(
    upstream_base_urls: tuple[str, ...],
    *,
    timeout_seconds: int = 5,
    auth_token: str | None = None,
    auth_tokens_by_base_url: dict[str, str] | None = None,
    tls_ca_file: str | None = None,
    tls_insecure_skip_verify: bool = False,
    fetch_json: Callable[[str, str | None], dict] | None = None,
) -> dict:
    delegated_fetch = fetch_json or (
        lambda url, token: _http_get_json(
            url,
            timeout_seconds=timeout_seconds,
            auth_token=token,
            tls_ca_file=tls_ca_file,
            tls_insecure_skip_verify=tls_insecure_skip_verify,
        )
    )
    return _core_fetch_dashboard_from_upstreams(
        upstream_base_urls,
        timeout_seconds=timeout_seconds,
        auth_token=auth_token,
        auth_tokens_by_base_url=auth_tokens_by_base_url,
        tls_ca_file=tls_ca_file,
        tls_insecure_skip_verify=tls_insecure_skip_verify,
        fetch_json=delegated_fetch,
        normalize_base_url_func=_normalize_base_url,
    )


def fetch_topic_from_upstreams(
    upstream_base_urls: tuple[str, ...],
    *,
    topic_id: str,
    timeout_seconds: int = 5,
    auth_token: str | None = None,
    auth_tokens_by_base_url: dict[str, str] | None = None,
    tls_ca_file: str | None = None,
    tls_insecure_skip_verify: bool = False,
    fetch_json: Callable[[str, str | None], dict] | None = None,
) -> dict:
    delegated_fetch = fetch_json or (
        lambda url, token: _http_get_json(
            url,
            timeout_seconds=timeout_seconds,
            auth_token=token,
            tls_ca_file=tls_ca_file,
            tls_insecure_skip_verify=tls_insecure_skip_verify,
        )
    )
    return _core_fetch_topic_from_upstreams(
        upstream_base_urls,
        topic_id=topic_id,
        timeout_seconds=timeout_seconds,
        auth_token=auth_token,
        auth_tokens_by_base_url=auth_tokens_by_base_url,
        tls_ca_file=tls_ca_file,
        tls_insecure_skip_verify=tls_insecure_skip_verify,
        fetch_json=delegated_fetch,
        normalize_base_url_func=_normalize_base_url,
    )


def fetch_topic_posts_from_upstreams(
    upstream_base_urls: tuple[str, ...],
    *,
    topic_id: str,
    limit: int = 120,
    timeout_seconds: int = 5,
    auth_token: str | None = None,
    auth_tokens_by_base_url: dict[str, str] | None = None,
    tls_ca_file: str | None = None,
    tls_insecure_skip_verify: bool = False,
    fetch_json: Callable[[str, str | None], dict] | None = None,
) -> list[dict]:
    delegated_fetch = fetch_json or (
        lambda url, token: _http_get_json(
            url,
            timeout_seconds=timeout_seconds,
            auth_token=token,
            tls_ca_file=tls_ca_file,
            tls_insecure_skip_verify=tls_insecure_skip_verify,
        )
    )
    return _core_fetch_topic_posts_from_upstreams(
        upstream_base_urls,
        topic_id=topic_id,
        limit=limit,
        timeout_seconds=timeout_seconds,
        auth_token=auth_token,
        auth_tokens_by_base_url=auth_tokens_by_base_url,
        tls_ca_file=tls_ca_file,
        tls_insecure_skip_verify=tls_insecure_skip_verify,
        fetch_json=delegated_fetch,
        normalize_base_url_func=_normalize_base_url,
    )


def build_server(config: BrainHiveWatchServerConfig | None = None) -> ThreadingHTTPServer:
    cfg = config or BrainHiveWatchServerConfig()
    return build_watch_server(
        cfg,
        workstation_version=NULLA_WORKSTATION_DEPLOYMENT_VERSION,
        server_factory=ThreadingHTTPServer,
        validate_tls_config=lambda inner_cfg: _validate_tls_config(inner_cfg),
        requires_public_tls=lambda host: _requires_public_tls(host),
        watch_tls_enabled=lambda inner_cfg: _watch_tls_enabled(inner_cfg),
        fetch_dashboard_from_upstreams=lambda *args, **kwargs: fetch_dashboard_from_upstreams(*args, **kwargs),
        fetch_topic_from_upstreams=lambda *args, **kwargs: fetch_topic_from_upstreams(*args, **kwargs),
        fetch_topic_posts_from_upstreams=lambda *args, **kwargs: fetch_topic_posts_from_upstreams(*args, **kwargs),
        proxy_nullabook_get=lambda *args, **kwargs: _proxy_nullabook_get(*args, **kwargs),
        http_get_json=lambda *args, **kwargs: _http_get_json(*args, **kwargs),
        normalize_base_url=lambda url: _normalize_base_url(url),
        ssl_context_for_url=lambda *args, **kwargs: _ssl_context_for_url(*args, **kwargs),
        build_tls_context=lambda inner_cfg: _build_tls_context(inner_cfg),
    )


def serve(config: BrainHiveWatchServerConfig | None = None) -> None:
    server = build_server(config)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _normalize_base_url(url: str) -> str:
    return _core_normalize_base_url(url)


def _requires_public_tls(host: str) -> bool:
    return _core_requires_public_tls(host)


def _watch_tls_enabled(cfg: BrainHiveWatchServerConfig) -> bool:
    return _core_watch_tls_enabled(cfg)


def _ssl_context_for_url(
    url: str,
    *,
    tls_ca_file: str | None = None,
    tls_insecure_skip_verify: bool = False,
) -> ssl.SSLContext | None:
    return _core_ssl_context_for_url(
        url,
        tls_ca_file=tls_ca_file,
        tls_insecure_skip_verify=tls_insecure_skip_verify,
    )


def _build_tls_context(cfg: BrainHiveWatchServerConfig) -> ssl.SSLContext | None:
    return _core_build_tls_context(cfg)


def _validate_tls_config(cfg: BrainHiveWatchServerConfig) -> None:
    _core_validate_tls_config(cfg)
