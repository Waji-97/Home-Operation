from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Notion
    notion_token: str = ""
    notion_database_id: str = ""
    notion_version: str = "2022-06-28"

    # Property names — must match the Notion database columns exactly.
    prop_title: str = "title"
    prop_slug: str = "slug"
    prop_status: str = "status"
    prop_type: str = "type"
    prop_tags: str = "tags"
    prop_updated: str = "updated"

    status_public_value: str = "Public"
    type_post_value: str = "Post"
    type_note_value: str = "Note"

    # Webhook
    notion_webhook_secret: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600

    # Listing
    page_size: int = 9

    # Site
    site_title: str = "devops notes"
    site_description: str = "Blogs and notes from the homelab."
    site_author: str = "waji"

    @property
    def use_mock(self) -> bool:
        """No real Notion credentials -> serve built-in sample content."""
        return not (self.notion_token and self.notion_database_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()
