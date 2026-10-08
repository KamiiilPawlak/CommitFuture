from app.services.cv_pipeline.transform.dictionaries.validator import TechStackValidator


def test_normalize_synonyms() -> None:
    validator = TechStackValidator()
    assert validator.normalize_skill("js") == "javascript"
    assert validator.normalize_skill("React.JS") == "react"
    assert validator.normalize_skill("python3") == "python"


def test_validate_and_deduplicate_skills() -> None:
    validator = TechStackValidator()
    raw_skills = ["js", "JavaScript", "react", "React.js", "unknown_tool"]

    result = validator.validate_skills(raw_skills)

    # Usuwa nieznane, scala synonimy i zwraca unikalne kanoniczne nazwy
    assert result == ["javascript", "react"]
