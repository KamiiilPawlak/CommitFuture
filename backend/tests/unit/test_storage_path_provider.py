from pathlib import Path

from freezegun import freeze_time

from app.services.ingestion_service.storage_path_provider import DateBasedPathProvider


def test_date_based_path_provider_creates_correct_month_directories(
    tmp_path: Path,
) -> None:

    base_dir = tmp_path / "storage"
    provider = DateBasedPathProvider(base_dir=base_dir)

    with freeze_time("2026-03-15"):
        target_dir_march = provider.get_target_dir()

        assert target_dir_march == base_dir / "marzec"
        assert target_dir_march.exists()
        assert target_dir_march.is_dir()

    with freeze_time("2026-04-01"):
        target_dir_april = provider.get_target_dir()

        assert target_dir_april == base_dir / "kwiecien"
        assert target_dir_april.exists()
        assert target_dir_april.is_dir()

    created_directories = [p.name for p in base_dir.iterdir() if p.is_dir()]
    assert sorted(created_directories) == ["kwiecien", "marzec"]
