"""Pydantic v2 response models for the OpenSincera API.

Public classes (`Publisher`, `DeviceMetrics`) are re-exported from the
package's `__init__.py` for ergonomic type-annotation use.

`extra="allow"` is set on every model so unknown fields the API may add in
the future are accepted silently rather than crashing existing clients.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _BaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class DeviceMetrics(_BaseModel):
    """Per-device-type metrics nested under `Publisher.device_level_metrics`."""

    average_refresh_rate: float
    avg_ad_units_in_view: float
    avg_ads_to_content_ratio: float
    max_refresh_rate: float
    min_refresh_rate: float
    max_ad_units_in_view: float
    max_ads_to_content_ratio: float
    min_ads_to_content_ratio: float
    percentage_of_ad_slots_with_refresh: float


class Publisher(_BaseModel):
    """A publisher record from `GET /api/publishers?id=…` or `?domain=…`."""

    publisher_id: int
    name: str
    visit_enabled: bool
    status: str
    primary_supply_type: str
    domain: str
    pub_description: str | None = None
    categories: list[str]
    slug: str
    avg_ads_to_content_ratio: float
    avg_ads_in_view: float
    avg_ad_refresh: float
    device_level_metrics: dict[str, DeviceMetrics]
    total_unique_gpids: int
    id_absorption_rate: float
    avg_page_weight: float
    avg_cpu: float
    total_supply_paths: int
    reseller_count: int
    parent_entity_id: int | None = None
    owner_domain: str | None = None
    updated_at: datetime
    similar_publishers: dict[str, list[int]]
