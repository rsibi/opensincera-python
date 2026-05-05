"""Pydantic v2 response models for the OpenSincera API.

Public classes (`Publisher`, `DeviceMetrics`) are re-exported from the
package's `__init__.py` for ergonomic type-annotation use.

`extra="allow"` is set on every model so unknown fields the API may add in
the future are accepted silently rather than crashing existing clients.

Field nullability is permissive on purpose: real responses include `null`
for many numeric/categorical fields (refresh rates, categories, etc.)
depending on how thoroughly the publisher has been scraped. Only
`publisher_id`, `name`, and `domain` are strictly required — those are
identity fields every record has. Everything else defaults to `None` so
the library never raises on a sparse-but-valid response.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _BaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class DeviceMetrics(_BaseModel):
    """Per-device-type metrics nested under `Publisher.device_level_metrics`."""

    average_refresh_rate: float | None = None
    avg_ad_units_in_view: float | None = None
    avg_ads_to_content_ratio: float | None = None
    max_refresh_rate: float | None = None
    min_refresh_rate: float | None = None
    max_ad_units_in_view: float | None = None
    max_ads_to_content_ratio: float | None = None
    min_ads_to_content_ratio: float | None = None
    percentage_of_ad_slots_with_refresh: float | None = None


class Publisher(_BaseModel):
    """A publisher record from `GET /api/publishers?id=…` or `?domain=…`."""

    publisher_id: int
    name: str
    domain: str
    visit_enabled: bool | None = None
    status: str | None = None
    primary_supply_type: str | None = None
    pub_description: str | None = None
    categories: list[str] | None = None
    slug: str | None = None
    avg_ads_to_content_ratio: float | None = None
    avg_ads_in_view: float | None = None
    avg_ad_refresh: float | None = None
    device_level_metrics: dict[str, DeviceMetrics] | None = None
    total_unique_gpids: int | None = None
    id_absorption_rate: float | None = None
    avg_page_weight: float | None = None
    avg_cpu: float | None = None
    total_supply_paths: int | None = None
    reseller_count: int | None = None
    parent_entity_id: int | None = None
    owner_domain: str | None = None
    updated_at: datetime | None = None
    similar_publishers: dict[str, list[int]] | None = None
