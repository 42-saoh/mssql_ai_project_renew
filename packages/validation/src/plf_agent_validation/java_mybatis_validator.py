from __future__ import annotations


def validate_java_mybatis_bundle(files: dict[str, str]) -> tuple[bool, list[str]]:
    required_suffixes = ["Dto.java", "Service.java", "Mapper.java", "Mapper.xml"]
    names = list(files)
    blockers = []
    for suffix in required_suffixes:
        if not any(name.endswith(suffix) for name in names):
            blockers.append(f"MISSING_{suffix}")
    for name, content in files.items():
        if "TODO: REVIEW_REQUIRED" not in content and "REVIEW_REQUIRED" not in content:
            blockers.append(f"MISSING_REVIEW_MARKER:{name}")
    return not blockers, blockers
