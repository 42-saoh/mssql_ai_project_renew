from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Iterable

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
CSS_PATH = ROOT / "styles" / "design.css"


def configure_page(title: str) -> None:
    st.set_page_config(
        page_title=f"{title} | PLF DB Agent V2",
        page_icon="DB",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_design_css()


def load_design_css() -> None:
    if not CSS_PATH.exists():
        return
    css = CSS_PATH.read_text(encoding="utf-8")
    body = f"<style>{css}</style>"
    if hasattr(st, "html"):
        st.html(body)
    else:  # pragma: no cover - compatibility fallback
        st.markdown(body, unsafe_allow_html=True)


def badge(label: str, tone: str = "info") -> str:
    safe_tone = tone if tone in {"draft", "warning", "success", "danger", "info"} else "info"
    return f'<span class="agent-badge agent-badge-{safe_tone}">{escape(label)}</span>'


def render_badges(items: Iterable[tuple[str, str]]) -> None:
    st.markdown(" ".join(badge(label, tone) for label, tone in items), unsafe_allow_html=True)


def render_sidebar(active: str) -> None:
    with st.sidebar:
        st.markdown("### PLF DB Agent V2")
        st.caption("Internal review console")
        st.divider()
        st.markdown("**Current view**")
        st.markdown(badge(active, "info"), unsafe_allow_html=True)
        st.divider()
        st.markdown("**Boundary**")
        st.caption("Streamlit uses FastAPI only. DB, MCP, and runner access stay behind platform services.")
        st.markdown(badge("API ONLY", "success"), unsafe_allow_html=True)


def render_header(title: str, caption: str, badges: Iterable[tuple[str, str]] = ()) -> None:
    st.title(title)
    st.caption(caption)
    items = list(badges)
    if items:
        render_badges(items)


def render_status_grid(items: Iterable[tuple[str, str]]) -> None:
    columns = st.columns(3)
    for column, (label, value) in zip(columns, items, strict=False):
        with column:
            st.markdown(
                (
                    '<div class="agent-status-item">'
                    f'<div class="agent-status-label">{escape(label)}</div>'
                    f'<div class="agent-status-value">{escape(value)}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def render_empty_state(title: str, body: str) -> None:
    st.markdown(
        (
            '<div class="agent-preview-empty">'
            f'<div class="agent-section-title">{escape(title)}</div>'
            f'<div>{escape(body)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )
