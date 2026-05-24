# Streamlit Design Contract

Root `DESIGN.md` is the authoritative UI contract for PLF DB Agent V2 Streamlit work in the Development Codex Realm.

## Required Use

Read `DESIGN.md` before changing Streamlit screens, CSS, layout, forms, charts, technical previews, or generated-output review panels. Streamlit UI should remain a restrained black-and-white internal console with native Streamlit primitives first and light CSS utilities second.

## Boundaries

- Streamlit calls FastAPI only through the local API client.
- Streamlit must not call DB, MSSQL MCP, Metadata Gateway, or Service Codex Runner directly.
- Root `DESIGN.md` is not inherited by Service Codex Runner runtime workspaces.
- Generated outputs must stay review-oriented and visibly marked as draft, manual review required, validated, blocked, or failed.

## Wording

Safe action labels include `Generate preview`, `Run analysis`, `Validate draft`, `Review evidence`, `Download preview`, `Refresh status`, and `Clear inputs`.

Do not add labels that imply unsafe automation, including `Execute SQL`, `Apply DDL`, `Deploy`, `Run stored procedure`, `Auto-fix database`, or `Overwrite source`.

## Required Files

- `.streamlit/config.toml` maps supported Streamlit theme tokens from `DESIGN.md`.
- `styles/design.css` contains stable utility classes only.
- Streamlit pages use wide layout and visible state for empty, loading, warning, blocked, and failed sections.
