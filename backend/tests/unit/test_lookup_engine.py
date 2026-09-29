from app.services.etl_cv_service.heuristic.dictionary.lookup_engine import (
    FlashLookupEngine,
)


def test_flash_lookup_engine_canonical_mapping() -> None:
    mock_dictionary: dict[str, list[str]] = {
        "Python": ["python", "py3", "python3"],
        "FastAPI": ["fastapi", "fast-api"],
        "Kubernetes": ["k8s", "kubernetes"],
        "Docker": ["docker"],
    }

    engine: FlashLookupEngine = FlashLookupEngine(keywords_map=mock_dictionary)

    test_text: str = "programista zna py3, fast-api, k8s i DOCKER"

    results: list[str] = engine.extract_matches(test_text)

    assert "Python" in results
    assert "FastAPI" in results
    assert "Kubernetes" in results

    # test case sensitivity off
    assert "Docker" in results
    assert len(results) == 4


def test_flash_lookup_engine_word_boundaries_no_false_positives() -> None:
    mock_dictionary: dict[str, list[str]] = {
        "Go": ["go"],
        "C": ["c"],
    }

    engine: FlashLookupEngine = FlashLookupEngine(keywords_map=mock_dictionary)

    test_text: str = "Programista django tworzy funkcje action w firmie"

    results: list[str] = engine.extract_matches(test_text)

    assert "Go" not in results
    assert "C" not in results
    assert results == []
