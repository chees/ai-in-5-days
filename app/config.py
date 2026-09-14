"""Application configuration and Secure Secret Management (Criteria 19).

Provides centralized configuration loading credentials securely from Google Cloud
Secret Manager when running in production, with local environment variable fallbacks.
Guarantees zero hardcoded credentials in the repository.
"""

import os
from typing import Optional
from google.cloud import secretmanager
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration schema."""
    project_id: str = Field(default_factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT", "saycheese-playground"))
    region: str = Field(default_factory=lambda: os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"))
    fast_model: str = Field(default_factory=lambda: os.getenv("FAST_MODEL", "gemini-2.5-flash"))
    reasoning_model: str = Field(default_factory=lambda: os.getenv("REASONING_MODEL", "gemini-2.5-pro"))
    use_secret_manager: bool = Field(default_factory=lambda: os.getenv("USE_SECRET_MANAGER", "false").lower() == "true")
    environment: str = Field(default_factory=lambda: os.getenv("ENV", "development"))


def get_secret(secret_id: str, project_id: Optional[str] = None, fallback_env: Optional[str] = None) -> str:
    """Securely fetches a secret from Google Cloud Secret Manager with env var fallback.

    Args:
        secret_id: The ID of the secret in Secret Manager.
        project_id: The Google Cloud project ID hosting the secret.
        fallback_env: Optional environment variable name to fall back to if Secret Manager is not active.

    Returns:
        The secret payload string.
    """
    config = AppConfig()
    target_project = project_id or config.project_id

    # Fallback to local environment variable if Secret Manager disabled or in dev
    if not config.use_secret_manager:
        if fallback_env and fallback_env in os.environ:
            return os.environ[fallback_env]
        return os.environ.get(secret_id, "")

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{target_project}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        # Graceful fallback to env if cloud secret retrieval fails
        if fallback_env and fallback_env in os.environ:
            return os.environ[fallback_env]
        raise RuntimeError(
            f"Failed to access secret '{secret_id}' from Secret Manager and no local fallback available: {e}"
        ) from e


# Global configuration instance
config = AppConfig()
