from __future__ import annotations

import base64
import importlib
import json

import network.signer as signer_mod


def _configure_signer_paths(tmp_path) -> None:
    signer_mod._KEY_DIR = tmp_path / "keys"
    signer_mod._LEGACY_PRIV_KEY_PATH = signer_mod._KEY_DIR / "node_signing_key.b64"
    signer_mod._KEY_RECORD_PATH = signer_mod._KEY_DIR / "node_signing_key.json"
    signer_mod._KEY_ARCHIVE_DIR = signer_mod._KEY_DIR / "archive"
    signer_mod._LOCAL_KEYPAIR = None


def _peer_id_for_seed(seed: bytes) -> str:
    signing_key = signer_mod._signing_key_from_seed(seed)
    verify_key = signer_mod._verify_key(signing_key)
    if signer_mod._SIGNER_BACKEND == "pynacl":
        return verify_key.encode(encoder=signer_mod.encoding.HexEncoder).decode("utf-8")
    raw = verify_key.public_bytes(
        encoding=signer_mod.serialization.Encoding.Raw,
        format=signer_mod.serialization.PublicFormat.Raw,
    )
    return raw.hex()


def test_signer_uses_encrypted_record_when_passphrase_is_set(monkeypatch, tmp_path) -> None:
    importlib.reload(signer_mod)
    _configure_signer_paths(tmp_path)
    monkeypatch.setenv("NULLA_KEY_PASSPHRASE", "closed-test-secret")

    peer_id = signer_mod.get_local_peer_id()

    assert peer_id
    assert signer_mod.key_storage_mode() == "encrypted_file"
    assert signer_mod.local_key_path() == signer_mod._KEY_RECORD_PATH
    assert signer_mod._KEY_RECORD_PATH.exists()
    assert not signer_mod._LEGACY_PRIV_KEY_PATH.exists()

    payload = json.loads(signer_mod._KEY_RECORD_PATH.read_text(encoding="utf-8"))
    assert payload["format"] == "encrypted_seed"
    assert "ciphertext_b64" in payload
    assert payload["ciphertext_b64"] != ""

    signer_mod._LOCAL_KEYPAIR = None
    assert signer_mod.get_local_peer_id() == peer_id


def test_signer_migrates_legacy_seed_to_encrypted_record_when_passphrase_appears(monkeypatch, tmp_path) -> None:
    importlib.reload(signer_mod)
    _configure_signer_paths(tmp_path)
    seed = bytes(range(32))
    signer_mod._KEY_DIR.mkdir(parents=True, exist_ok=True)
    signer_mod._LEGACY_PRIV_KEY_PATH.write_text(base64.b64encode(seed).decode("utf-8"), encoding="utf-8")
    monkeypatch.setenv("NULLA_KEY_PASSPHRASE", "closed-test-secret")

    peer_id = signer_mod.get_local_peer_id()

    assert peer_id == _peer_id_for_seed(seed)
    assert signer_mod._KEY_RECORD_PATH.exists()
    assert not signer_mod._LEGACY_PRIV_KEY_PATH.exists()
    assert signer_mod.key_storage_mode() == "encrypted_file"


def test_signer_rejects_encrypted_record_without_passphrase(monkeypatch, tmp_path) -> None:
    importlib.reload(signer_mod)
    _configure_signer_paths(tmp_path)
    monkeypatch.setenv("NULLA_KEY_PASSPHRASE", "closed-test-secret")
    signer_mod.get_local_peer_id()
    signer_mod._LOCAL_KEYPAIR = None
    monkeypatch.delenv("NULLA_KEY_PASSPHRASE", raising=False)

    try:
        signer_mod.load_or_create_local_keypair()
    except RuntimeError as exc:
        assert "NULLA_KEY_PASSPHRASE" in str(exc)
    else:
        raise AssertionError("expected encrypted signer record to require NULLA_KEY_PASSPHRASE")


def test_rotate_local_keypair_preserves_encrypted_storage_and_archives_old_record(monkeypatch, tmp_path) -> None:
    importlib.reload(signer_mod)
    _configure_signer_paths(tmp_path)
    monkeypatch.setenv("NULLA_KEY_PASSPHRASE", "closed-test-secret")
    old_peer = signer_mod.get_local_peer_id()

    result = signer_mod.rotate_local_keypair()

    assert result["old_peer_id"] == old_peer
    assert result["new_peer_id"] != old_peer
    archived_path = result["archived_key_path"]
    assert archived_path.exists()
    assert archived_path.suffix == ".json"
    assert signer_mod._KEY_RECORD_PATH.exists()
    assert signer_mod.key_storage_mode() == "encrypted_file"
