IF OBJECT_ID(N'dbo.evidence_bundles', N'U') IS NULL
BEGIN
  CREATE TABLE dbo.evidence_bundles (
    evidence_bundle_id NVARCHAR(64) NOT NULL CONSTRAINT pk_evidence_bundles PRIMARY KEY,
    db_profile_id NVARCHAR(128) NOT NULL,
    target_key NVARCHAR(256) NOT NULL,
    evidence_hash CHAR(64) NOT NULL,
    content_ref NVARCHAR(512) NOT NULL,
    collected_at DATETIME2(3) NOT NULL
  );
END;
