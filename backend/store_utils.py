#!/usr/bin/env python3
"""Storage helper utilities for Star Office backend.

JSON load/save for agents state, asset positions/defaults, runtime config, and join keys.
"""

from __future__ import annotations

import json
import os


def _load_json(path: str):
    """Load JSON from a file; caller handles missing file or parse errors."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data):
    """Write data as JSON with UTF-8 and indent=2."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_agents_state(path: str, default_agents: list) -> list:
    """Load agents list from path; return default_agents if file missing or invalid."""
    if os.path.exists(path):
        try:
            data = _load_json(path)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return list(default_agents)


def save_agents_state(path: str, agents: list):
    """Persist agents list to path."""
    _save_json(path, agents)


def load_asset_positions(path: str) -> dict:
    """Load asset positions map from path; return {} if missing or invalid."""
    if os.path.exists(path):
        try:
            data = _load_json(path)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def save_asset_positions(path: str, data: dict):
    """Persist asset positions to path."""
    _save_json(path, data)


def load_asset_defaults(path: str) -> dict:
    """Load asset defaults map from path; return {} if missing or invalid."""
    if os.path.exists(path):
        try:
            data = _load_json(path)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def save_asset_defaults(path: str, data: dict):
    """Persist asset defaults to path."""
    _save_json(path, data)


def _normalize_user_model(model_name: str) -> str:
    """Map provider model names to canonical user-facing options (seedream-5-lite / seedream-5)."""
    m = (model_name or "").strip().lower()
    if m in {"seedream-5-lite", "seedream-5"}:
        return m
    if m in {"doubao-seedream-5-0-260128"}:
        return "seedream-5-lite"
    return "seedream-5-lite"


def load_runtime_config(path: str) -> dict:
    """Load runtime config (seedream_api_key, seedream_model) from env and optional JSON file."""
    base = {
        "seedream_api_key": os.getenv("SEEDREAM_API_KEY") or os.getenv("GEMINI_API_KEY") or "",
        "seedream_model": _normalize_user_model(os.getenv("SEEDREAM_MODEL") or os.getenv("GEMINI_MODEL") or "seedream-5-lite"),
    }
    if os.path.exists(path):
        try:
            data = _load_json(path)
            if isinstance(data, dict):
                key = data.get("seedream_api_key") or data.get("gemini_api_key") or base["seedream_api_key"]
                model = data.get("seedream_model") or data.get("gemini_model") or base["seedream_model"]
                base["seedream_api_key"] = key
                base["seedream_model"] = _normalize_user_model(model)
        except Exception:
            pass
    return base


def save_runtime_config(path: str, data: dict):
    """Merge data into current runtime config and save to path; chmod 0o600 on path."""
    cfg = load_runtime_config(path)
    cfg.update(data or {})
    _save_json(path, cfg)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def load_join_keys(path: str) -> dict:
    """Load join keys structure from path; return {'keys': []} if missing or invalid."""
    if os.path.exists(path):
        try:
            data = _load_json(path)
            if isinstance(data, dict) and isinstance(data.get("keys"), list):
                return data
        except Exception:
            pass
    return {"keys": []}


def save_join_keys(path: str, data: dict):
    """Persist join keys to path."""
    _save_json(path, data)
