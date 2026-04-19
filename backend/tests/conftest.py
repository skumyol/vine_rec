"""Pytest configuration and fixtures."""

import pytest
from app.models.sku import ParsedSKU, WineSKUInput


@pytest.fixture
def sample_parsed_sku():
    """Sample parsed Burgundy SKU."""
    return ParsedSKU(
        raw_name="Domaine Rossignol-Trapet Latricieres-Chambertin Grand Cru 2017",
        producer="Domaine Rossignol-Trapet",
        producer_normalized="domaine rossignol trapet",
        appellation="Latricieres-Chambertin",
        appellation_normalized="latricieres chambertin",
        vineyard="Latricieres-Chambertin",
        vineyard_normalized="latricieres chambertin",
        classification="Grand Cru",
        classification_normalized="grand cru",
        vintage="2017",
        region="Burgundy",
        normalized_tokens=["domaine", "rossignol", "trapet", "latricieres", "chambertin", "grand", "cru", "2017"]
    )


@pytest.fixture
def sample_wine_input():
    """Sample wine input."""
    return WineSKUInput(
        wine_name="Domaine Arlaud Morey-St-Denis Monts Luisants 1er Cru",
        vintage="2019",
        format="750ml",
        region="Burgundy"
    )


@pytest.fixture
def sample_queries():
    """Sample search queries."""
    from app.models.sku import SearchQuery
    return [
        SearchQuery(query="domaine arlaud morey saint denis 2019 bottle", query_type="exact", priority=1),
        SearchQuery(query="domaine arlaud morey saint denis 2019", query_type="relaxed", priority=2),
    ]
