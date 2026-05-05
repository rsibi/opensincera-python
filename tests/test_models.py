"""Tests for the response models in `opensincera._models`.

The `SAMPLE_PUBLISHER` fixture mirrors the example response from the official
OpenSincera API docs verbatim, so any future schema drift the docs publish
should land here first.
"""

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from opensincera._models import DeviceMetrics, Publisher

SAMPLE_PUBLISHER: dict[str, Any] = {
    "publisher_id": 1,
    "name": "Business Insider",
    "visit_enabled": True,
    "status": "available",
    "primary_supply_type": "web",
    "domain": "businessinsider.com",
    "pub_description": (
        "Business Insider tells the global tech, finance, stock market, "
        "media, economy, lifestyle, real estate, AI and innovative stories "
        "you want to know."
    ),
    "categories": [
        "General",
        "Business and Finance",
        "Technology & Computing",
        "Personal Finance",
        "Law",
        "Business",
        "Computing",
    ],
    "slug": "business-insider",
    "avg_ads_to_content_ratio": 0.20525,
    "avg_ads_in_view": 2.02004,
    "avg_ad_refresh": 70.896,
    "device_level_metrics": {
        "mobile": {
            "average_refresh_rate": 53.704,
            "avg_ad_units_in_view": 1.60285,
            "avg_ads_to_content_ratio": 0.21721,
            "max_refresh_rate": 295.0,
            "min_refresh_rate": 20.0,
            "max_ad_units_in_view": 4.0,
            "max_ads_to_content_ratio": 1.0,
            "min_ads_to_content_ratio": 0.0,
            "percentage_of_ad_slots_with_refresh": 100.0,
        },
        "desktop": {
            "average_refresh_rate": 56.25,
            "avg_ad_units_in_view": 2.37945,
            "avg_ads_to_content_ratio": 0.19513,
            "max_refresh_rate": 205.0,
            "min_refresh_rate": 5.0,
            "max_ad_units_in_view": 12.0246,
            "max_ads_to_content_ratio": 1.0,
            "min_ads_to_content_ratio": 0.0,
            "percentage_of_ad_slots_with_refresh": 91.23,
        },
    },
    "total_unique_gpids": 926,
    "id_absorption_rate": 0.375,
    "avg_page_weight": 27.8427,
    "avg_cpu": 254.6705,
    "total_supply_paths": 123,
    "reseller_count": 70,
    "parent_entity_id": 59072,
    "owner_domain": "insider-inc.com",
    "updated_at": "2026-01-06T01:00:28.820Z",
    "similar_publishers": {"content": [41, 67, 405, 700]},
}


class TestPublisher:
    def test_validates_from_official_sample(self) -> None:
        pub = Publisher.model_validate(SAMPLE_PUBLISHER)
        assert pub.publisher_id == 1
        assert pub.name == "Business Insider"
        assert pub.domain == "businessinsider.com"
        assert pub.visit_enabled is True
        assert pub.status == "available"
        assert pub.primary_supply_type == "web"
        assert pub.avg_ads_to_content_ratio == 0.20525
        assert pub.total_supply_paths == 123

    def test_parses_updated_at_as_datetime(self) -> None:
        pub = Publisher.model_validate(SAMPLE_PUBLISHER)
        assert isinstance(pub.updated_at, datetime)

    def test_device_metrics_are_typed(self) -> None:
        pub = Publisher.model_validate(SAMPLE_PUBLISHER)
        mobile = pub.device_level_metrics["mobile"]
        assert isinstance(mobile, DeviceMetrics)
        assert mobile.average_refresh_rate == 53.704

    def test_accepts_unknown_top_level_fields(self) -> None:
        payload = {**SAMPLE_PUBLISHER, "future_field_we_dont_know_about": 42}
        # Should not raise.
        Publisher.model_validate(payload)

    def test_optional_fields_default_to_none(self) -> None:
        payload = {
            k: v
            for k, v in SAMPLE_PUBLISHER.items()
            if k not in {"pub_description", "owner_domain", "parent_entity_id"}
        }
        pub = Publisher.model_validate(payload)
        assert pub.pub_description is None
        assert pub.owner_domain is None
        assert pub.parent_entity_id is None

    def test_rejects_missing_required_field(self) -> None:
        payload = {k: v for k, v in SAMPLE_PUBLISHER.items() if k != "publisher_id"}
        with pytest.raises(ValidationError):
            Publisher.model_validate(payload)

    def test_categories_is_a_list_of_strings(self) -> None:
        pub = Publisher.model_validate(SAMPLE_PUBLISHER)
        assert pub.categories == [
            "General",
            "Business and Finance",
            "Technology & Computing",
            "Personal Finance",
            "Law",
            "Business",
            "Computing",
        ]

    def test_similar_publishers_keeps_grouping(self) -> None:
        pub = Publisher.model_validate(SAMPLE_PUBLISHER)
        assert pub.similar_publishers == {"content": [41, 67, 405, 700]}


class TestDeviceMetrics:
    def test_validates_standalone(self) -> None:
        dm = DeviceMetrics.model_validate(SAMPLE_PUBLISHER["device_level_metrics"]["mobile"])
        assert dm.average_refresh_rate == 53.704
        assert dm.percentage_of_ad_slots_with_refresh == 100.0
