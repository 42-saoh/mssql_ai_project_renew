from __future__ import annotations

JAVA_MYBATIS_SUFFIX_BY_ARTIFACT_TYPE = {
    "DTO_DRAFT": "Dto.java",
    "SERVICE_DRAFT": "Service.java",
    "MAPPER_INTERFACE": "Mapper.java",
    "MAPPER_XML": "Mapper.xml",
}


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


def validate_java_mybatis_artifact(artifact_type: str, artifact: dict) -> tuple[bool, list[str]]:
    suffix = JAVA_MYBATIS_SUFFIX_BY_ARTIFACT_TYPE.get(artifact_type)
    if suffix is None:
        return True, []

    blockers: list[str] = []
    content = str(artifact.get("contentMarkdown") or "")
    if "REVIEW_REQUIRED" not in content:
        blockers.append("MISSING_REVIEW_MARKER_IN_CONTENT")

    file_name = str(artifact.get("fileName") or "")
    if file_name and not file_name.endswith(suffix):
        blockers.append(f"JAVA_MYBATIS_FILE_SUFFIX_MISMATCH:{suffix}")

    files = artifact.get("files")
    if isinstance(files, dict) and files:
        normalized = {str(name): str(body) for name, body in files.items()}
        if not any(name.endswith(suffix) for name in normalized):
            blockers.append(f"MISSING_{suffix}")
        for name, file_content in normalized.items():
            if "TODO: REVIEW_REQUIRED" not in file_content and "REVIEW_REQUIRED" not in file_content:
                blockers.append(f"MISSING_REVIEW_MARKER:{name}")

    return not blockers, blockers
