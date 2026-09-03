from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelConfig:
    name: str
    env_key: str
    model: str


MODELS: dict[str, ModelConfig] = {
    "fast": ModelConfig(
        name="fast",
        env_key="NEMOTRON_3_5_SUPER_API",
        model="nvidia/nemotron-3-super-120b-a12b",
    ),
    "medium": ModelConfig(
        name="medium",
        env_key="NEMOTRON_3_ULTRA_API",
        model="nvidia/nemotron-3-ultra-550b-a55b",
    ),
    "deep": ModelConfig(
        name="deep",
        env_key="DEEPSEEK_API",
        model="deepseek-ai/deepseek-v4-pro-0813",
    ),
}


DEFAULT_MODEL = "fast"


def get_model(name: str) -> ModelConfig:
    try:
        return MODELS[name]
    except KeyError as exc:
        raise ValueError(
            f"unknown model '{name}' "
            "(expected: fast, medium, deep)"
        ) from exc


def get_api_key(config: ModelConfig) -> str:
    api_key = os.getenv(config.env_key)

    if not api_key:
        raise RuntimeError(
            f"{config.env_key} is not configured"
        )

    return api_key


def get_base_url() -> str:
    base_url = os.getenv("BASE_URL")

    if not base_url:
        raise RuntimeError(
            "BASE_URL is not configured"
        )

    return base_url
