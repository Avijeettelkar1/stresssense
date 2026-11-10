"""Recommender prototype UI (Streamlit). Owner: C.

Run:  streamlit run src/recommender/app.py
Reads decisions.csv (mock by default), walks the adaptive survey, and shows a suggestion.
This is a demo scaffold for M4 — flesh out styling and the end-to-end flow here.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from src.common import io
from src.recommender.recommender import recommend
from src.recommender.survey import next_question


def run():
    st.set_page_config(page_title="StressSense", page_icon="🫁")
    st.title("StressSense — recommendation prototype")
    st.caption("Non-clinical well-being nudges only. Not a diagnostic tool.")

    use_mock = st.sidebar.checkbox("Use mock decisions", value=True)
    decisions = io.read_table("decisions", use_mock=use_mock)

    subject = st.sidebar.selectbox("Subject", sorted(decisions["subject_id"].unique()))
    sub = decisions[decisions["subject_id"] == subject]
    window = st.sidebar.selectbox("Window", sorted(sub["window_id"].unique()))
    row = sub[sub["window_id"] == window].iloc[0]

    st.metric("Gate decision", row["decision"], help=f"adjusted score {row['adjusted_score']:.2f}")

    # Adaptive survey -> context
    answers: dict = {}
    if "minutes_available" not in answers:
        answers["minutes_available"] = st.number_input("Minutes available", 0, 120, 10)
    q = next_question(answers)
    if q and q["id"] == "can_leave_desk":
        answers["can_leave_desk"] = st.checkbox("Can step away from desk")
    q = next_question(answers)
    if q and q["id"] == "prefers":
        answers["prefers"] = st.selectbox("Preference", ["(no preference)"] + q["choices"])
        if answers["prefers"] == "(no preference)":
            answers.pop("prefers")

    st.subheader("Suggestion")
    st.success(recommend(row["decision"], answers))


if __name__ == "__main__":
    run()
