from .lookup_engine import FlashLookupEngine

# Wyłącznie formalne certyfikaty/egzaminy/dyplomy - celowo NIE zawiera nazw
# samych technologii (Docker, REST itd.), żeby odróżnić certyfikat od
# umiejętności technicznej bez pomocy LLM.
CERTIFICATIONS_DICTIONARY: dict[str, list[str]] = {
    "AWS Certified Solutions Architect": [
        "aws certified solutions architect",
        "aws solutions architect",
        "aws saa",
        "aws csa",
    ],
    "AWS Certified Developer": ["aws certified developer", "aws cda"],
    "AWS Certified SysOps Administrator": ["aws certified sysops administrator"],
    "AWS Certified DevOps Engineer": ["aws certified devops engineer"],
    "AWS Certified Cloud Practitioner": ["aws certified cloud practitioner", "aws ccp"],
    "Microsoft Certified: Azure Fundamentals": ["az-900", "azure fundamentals"],
    "Microsoft Certified: Azure Administrator": ["az-104", "azure administrator"],
    "Microsoft Certified: Azure Developer": ["az-204", "azure developer associate"],
    "Microsoft Certified: Azure Solutions Architect": [
        "az-305",
        "azure solutions architect expert",
    ],
    "Google Cloud Professional Cloud Architect": [
        "google cloud professional cloud architect",
        "gcp professional cloud architect",
    ],
    "Google Cloud Associate Cloud Engineer": [
        "google cloud associate cloud engineer",
        "gcp associate cloud engineer",
    ],
    "CKA (Certified Kubernetes Administrator)": [
        "cka",
        "certified kubernetes administrator",
    ],
    "CKAD (Certified Kubernetes Application Developer)": [
        "ckad",
        "certified kubernetes application developer",
    ],
    "PMP (Project Management Professional)": [
        "pmp",
        "project management professional",
    ],
    "PMI-ACP": ["pmi-acp"],
    "PRINCE2": ["prince2"],
    "Scrum Master (CSM/PSM)": [
        "csm",
        "psm",
        "psm i",
        "psm ii",
        "certified scrum master",
        "professional scrum master",
    ],
    "Product Owner (CSPO/PSPO)": [
        "cspo",
        "pspo",
        "certified scrum product owner",
        "professional scrum product owner",
    ],
    "SAFe Certified": ["safe certified", "scaled agile framework certified"],
    "ISTQB": ["istqb", "istqb certified tester"],
    "CCNA": ["ccna", "cisco certified network associate"],
    "CCNP": ["ccnp", "cisco certified network professional"],
    "CompTIA Security+": ["security+", "comptia security+"],
    "CompTIA Network+": ["network+", "comptia network+"],
    "CISSP": ["cissp"],
    "CISM": ["cism"],
    "CEH": ["ceh", "certified ethical hacker"],
    "OSCP": ["oscp", "offensive security certified professional"],
    "Oracle Certified Professional": ["ocp", "oracle certified professional"],
    "Oracle Certified Associate": ["oca", "oracle certified associate"],
    "ITIL": ["itil", "itil foundation", "itil v4"],
    "TOGAF": ["togaf"],
    "Six Sigma": ["six sigma", "lean six sigma"],
}

_certifications_engine = FlashLookupEngine(CERTIFICATIONS_DICTIONARY)


def extract_certifications(text: str) -> list[str]:
    return _certifications_engine.extract_matches(text)
