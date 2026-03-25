from __future__ import annotations

import os
from collections.abc import Mapping

from core.hardware_tier import probe_machine, select_qwen_tier
from core.model_registry import ModelRegistry
from storage.model_provider_manifest import ModelProviderManifest

_DEFAULT_KIMI_BASE_URL = "https://api.moonshot.ai/v1"
_DEFAULT_KIMI_MODEL = "kimi-k2"


def default_runtime_model_tag() -> str:
    return str(select_qwen_tier(probe_machine()).ollama_tag or "").strip() or "qwen2.5:7b"


def ensure_default_runtime_providers(
    registry: ModelRegistry,
    *,
    model_tag: str | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    env_map = os.environ if env is None else env
    changed: list[str] = []
    local_model = str(model_tag or "").strip() or default_runtime_model_tag()
    if _ensure_local_ollama_provider(registry, model_tag=local_model):
        changed.append(f"ollama-local:{local_model}")
    kimi_provider_id = _ensure_kimi_provider(registry, env=env_map)
    if kimi_provider_id:
        changed.append(kimi_provider_id)
    return tuple(changed)


def _ensure_local_ollama_provider(registry: ModelRegistry, *, model_tag: str) -> bool:
    existing = registry.get_manifest("ollama-local", model_tag)
    existing_caps_raw = getattr(existing, "capabilities", ()) if existing is not None else ()
    if not isinstance(existing_caps_raw, (list, tuple, set)):
        existing_caps_raw = ()
    existing_caps = {str(item).strip().lower() for item in existing_caps_raw}
    has_license = bool(
        str(getattr(existing, "license_name", None) or "").strip()
        and str(getattr(existing, "resolved_license_reference", None) or "").strip()
    )
    if existing and existing.enabled and "tool_intent" in existing_caps and has_license:
        return False
    parameter_size = parameter_size_for_model(model_tag)
    manifest = ModelProviderManifest(
        provider_name="ollama-local",
        model_name=model_tag,
        source_type="http",
        adapter_type="local_qwen_provider",
        license_name="Apache-2.0",
        license_reference="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE",
        license_url_or_reference="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE",
        weight_location="external",
        runtime_dependency="ollama",
        notes=f"Local Qwen via Ollama ({parameter_size}) — auto-registered by NULLA runtime",
        capabilities=["summarize", "classify", "format", "extract", "code_basic", "structured_json", "tool_intent"],
        runtime_config={
            "base_url": "http://127.0.0.1:11434",
            "api_path": "/v1/chat/completions",
            "health_path": "/v1/models",
            "timeout_seconds": 180,
            "health_timeout_seconds": 10,
            "temperature": 0.7,
            "supports_json_mode": False,
        },
        metadata={
            "runtime_family": "ollama",
            "confidence_baseline": 0.65,
            "parameter_count": parameter_size,
            "orchestration_role": "drone",
            "deployment_class": "local",
            "tool_support": ["structured_json", "tool_calls"],
            "max_safe_concurrency": 1,
        },
        enabled=True,
    )
    registry.register_manifest(manifest)
    return True


def _ensure_kimi_provider(
    registry: ModelRegistry,
    *,
    env: Mapping[str, str],
) -> str:
    api_key = str(env.get("KIMI_API_KEY") or "").strip()
    if not api_key:
        return ""
    model_name = str(env.get("KIMI_MODEL") or env.get("NULLA_KIMI_MODEL") or _DEFAULT_KIMI_MODEL).strip() or _DEFAULT_KIMI_MODEL
    existing = registry.get_manifest("kimi-remote", model_name)
    has_base_url = bool(str(getattr(existing, "runtime_config", {}).get("base_url") or "").strip()) if existing else False
    if existing and existing.enabled and has_base_url:
        return existing.provider_id
    base_url = str(env.get("KIMI_BASE_URL") or env.get("NULLA_KIMI_BASE_URL") or _DEFAULT_KIMI_BASE_URL).strip() or _DEFAULT_KIMI_BASE_URL
    manifest = ModelProviderManifest(
        provider_name="kimi-remote",
        model_name=model_name,
        source_type="http",
        adapter_type="openai_compatible",
        license_name="Provider",
        license_reference="user-managed",
        license_url_or_reference="user-managed",
        weight_location="external",
        redistribution_allowed=False,
        runtime_dependency="remote-openai-compatible-provider",
        notes="Kimi via Moonshot OpenAI-compatible API — auto-registered when KIMI_API_KEY is configured.",
        capabilities=["summarize", "classify", "format", "extract", "code_basic", "code_complex", "structured_json", "long_context"],
        runtime_config={
            "base_url": base_url,
            "api_path": "/chat/completions",
            "health_path": "/models",
            "timeout_seconds": 180,
            "health_timeout_seconds": 10,
            "temperature": 0.3,
            "supports_json_mode": True,
            "api_key_env": "KIMI_API_KEY",
        },
        metadata={
            "runtime_family": "openai-compatible",
            "confidence_baseline": 0.78,
            "orchestration_role": "queen",
            "deployment_class": "remote",
            "context_window": 128000,
            "tool_support": ["structured_json", "code_complex"],
            "max_safe_concurrency": 2,
        },
        enabled=True,
    )
    registry.register_manifest(manifest)
    return manifest.provider_id


def parameter_size_for_model(model_tag: str) -> str:
    model_name = str(model_tag or "").strip().split("/", 1)[-1]
    if ":" not in model_name:
        return "7B"
    _, size = model_name.split(":", 1)
    return size.upper()


__all__ = [
    "default_runtime_model_tag",
    "ensure_default_runtime_providers",
]
