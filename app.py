"""
Job Application Agent — Streamlit Web UI.

Run: streamlit run app.py
"""

import ssl_patch  # must be first — patches REQUESTS_CA_BUNDLE for corporate proxies
import os
import re as _re_top
from datetime import datetime, timedelta
from pathlib import Path

import exa_py
import pandas as pd

import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv(
    "LANGCHAIN_TRACING_V2", "false"))
os.environ.setdefault("LANGCHAIN_PROJECT",    os.getenv(
    "LANGCHAIN_PROJECT", "job-application-agent"))

# ── Resolve profile paths for display ────────────────────────────────────────
_BASE = Path(__file__).parent
_IC_PATH = (_BASE / os.getenv("IC_PROFILE_PATH",
            "../Profile Summary - IC.txt")).resolve()
_LS_PATH = (_BASE / os.getenv("LEADERSHIP_PROFILE_PATH",
            "../Profile Summary-Leadership.txt")).resolve()

st.set_page_config(page_title="Job Application Agent",
                   page_icon="🤖", layout="wide")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    st.subheader("📄 Profiles in use")
    st.markdown(
        f"**IC:** `{_IC_PATH.name}`  \n"
        f"{'✅ found' if _IC_PATH.exists() else '❌ NOT FOUND'}  \n\n"
        f"**Leadership:** `{_LS_PATH.name}`  \n"
        f"{'✅ found' if _LS_PATH.exists() else '❌ NOT FOUND'}"
    )

    st.divider()
    st.subheader("Input method")
    input_mode = st.radio(
        "Input method",
        ["Job URL", "Job URLs (file)", "Paste JD text"],
        index=0,
        label_visibility="collapsed",
    )

    st.subheader("Options")
    if st.button("🔄 Refresh profile index"):
        with st.spinner("Re-indexing profiles into Chroma..."):
            from tools.vector_store import refresh_profiles as do_refresh
            do_refresh()
        st.success("Profiles re-indexed ✅")

    st.divider()
    st.caption("Stack: LangGraph · LlamaIndex · Exa · Chroma · Groq Llama 3.3")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_agent, tab_report = st.tabs(["🤖 Agent", "📊 Reports"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Agent
# ═══════════════════════════════════════════════════════════════════════════════
with tab_agent:
    st.title("🤖 Job Application Agent")
    st.caption(
        "Scores your IC & Leadership profiles against any job and identifies gaps.")

    job_url = pasted_text = ""
    job_urls_text = ""
    job_urls_file = None

    if input_mode == "Job URL":
        job_url = st.text_input(
            "Job URL", placeholder="https://linkedin.com/jobs/view/...")
    elif input_mode == "Job URLs (file)":
        st.info(
            "Collect job links yourself (from LinkedIn, Glassdoor, company sites — "
            "anywhere) into a **.txt file, one URL per line**, or paste them below. "
            "The agent opens each link, extracts the JD, and scores it. Blank lines "
            "and lines starting with `#` are ignored.",
            icon="💡",
        )
        job_urls_file = st.file_uploader(
            "Upload a .txt file of job URLs (one per line)",
            type=["txt", "csv"],
        )
        job_urls_text = st.text_area(
            "…or paste URLs here (one per line)",
            height=160,
            placeholder="https://www.linkedin.com/jobs/view/4438141560/\n"
                        "https://www.glassdoor.co.in/job-listing/...\n"
                        "https://careers.company.com/job/12345",
        )
    else:
        pasted_text = st.text_area(
            "Paste job description", height=300, placeholder="Paste the full JD here...")

    _bulk_mode = input_mode == "Job URLs (file)"
    _btn_label = "🔍  Find & Score All Jobs" if _bulk_mode else "▶️  Run Agent"
    run_btn = st.button(_btn_label, type="primary", use_container_width=True)

    if run_btn and input_mode == "Job URLs (file)":
        # ── Score a user-supplied list of job URLs, one by one ────────────────
        import re as _re_ul
        from agents.graph import graph as _graph
        import time as _time

        _raw_text = job_urls_text or ""
        if job_urls_file is not None:
            try:
                _raw_text += "\n" + job_urls_file.getvalue().decode(
                    "utf-8", errors="replace")
            except Exception as _fe:
                st.error(f"Couldn't read uploaded file: {_fe}")
                st.stop()

        # Extract URLs: accept whole lines that are URLs, or URLs embedded in a
        # line (e.g. CSV). De-dupe while preserving order.
        _url_list: list = []
        _seen_u: set = set()
        for _line in _raw_text.splitlines():
            _line = _line.strip()
            if not _line or _line.startswith("#"):
                continue
            for _m in _re_ul.findall(r'https?://[^\s,"\'<>]+', _line):
                _u = _m.rstrip('.,;)')
                if _u not in _seen_u:
                    _seen_u.add(_u)
                    _url_list.append(_u)

        if not _url_list:
            st.warning(
                "No URLs found. Upload a .txt file or paste at least one "
                "`http(s)://…` job link (one per line).")
            st.stop()

        st.info(
            f"📥 Loaded **{len(_url_list)}** job URL(s). Scoring one by one…")

        _all_scores = []
        _ul_expired = 0
        _progress_bar = st.progress(0)
        _status_txt = st.empty()
        _live_table = st.empty()

        _EXPIRED_MARKERS = (
            "job expired", "this job has expired", "no longer available",
            "no longer accepting applications", "applications are closed",
            "position has been filled", "this position is closed",
            "posting has expired", "not accepting applications",
        )

        for _i, _u in enumerate(_url_list):
            _hint = f"Job {_i+1}"
            _status_txt.markdown(f"⏳ Scoring {_i+1}/{len(_url_list)}: {_u}")
            if _i > 0:
                _time.sleep(4)

            _init_ul = {
                "job_url":          _u,
                "search_query":     "",
                "portal":           "",
                "job_source_url":   _u,
                "skip_cover":       True,
                "raw_jd":           "",
                "parsed_jd":        None,
                "ic_score":         None,
                "leadership_score": None,
                "best_profile":     None,
                "strengths":        [],
                "gaps":             [],
                "levers":           [],
                "cover_letter":     "",
                "ats_entry":        "",
                "messages":         [],
            }
            try:
                _merged_ul = {**_init_ul}
                for _step in _graph.stream(_init_ul, stream_mode="updates"):
                    _merged_ul.update(list(_step.values())[0])
                _pjd = _merged_ul.get("parsed_jd") or {}

                _jd_blob = (f"{_merged_ul.get('raw_jd', '')} "
                            f"{_pjd.get('title', '')}").lower()
                if any(_m in _jd_blob for _m in _EXPIRED_MARKERS):
                    _ul_expired += 1
                    _progress_bar.progress((_i + 1) / len(_url_list))
                    continue

                _ic = _merged_ul.get("ic_score") or 0
                _ls = _merged_ul.get("leadership_score") or 0
                _bp = _merged_ul.get("best_profile") or "IC"
                _all_scores.append({
                    "Title":   _pjd.get("title") or _hint,
                    "Company": _pjd.get("company", ""),
                    "IC": _ic, "LS": _ls, "Best": _bp,
                    "Score": _ic if _bp == "IC" else _ls,
                    "URL": _u,
                    "Gaps": ", ".join(_merged_ul.get("gaps") or []),
                })
            except Exception as _ex:
                _err_str = str(_ex)
                if "rate_limit" in _err_str.lower() or "429" in _err_str:
                    _status_txt.markdown(
                        f"⏳ Rate limited — waiting 20s then retrying {_i+1}…")
                    _time.sleep(20)
                    try:
                        _merged_ul = {**_init_ul}
                        for _step in _graph.stream(_init_ul, stream_mode="updates"):
                            _merged_ul.update(list(_step.values())[0])
                        _pjd = _merged_ul.get("parsed_jd") or {}
                        _ic = _merged_ul.get("ic_score") or 0
                        _ls = _merged_ul.get("leadership_score") or 0
                        _bp = _merged_ul.get("best_profile") or "IC"
                        _all_scores.append({
                            "Title":   _pjd.get("title") or _hint,
                            "Company": _pjd.get("company", ""),
                            "IC": _ic, "LS": _ls, "Best": _bp,
                            "Score": _ic if _bp == "IC" else _ls,
                            "URL": _u,
                            "Gaps": ", ".join(_merged_ul.get("gaps") or []),
                        })
                        _progress_bar.progress((_i + 1) / len(_url_list))
                        continue
                    except Exception as _ex2:
                        _err_str = str(_ex2)
                _err_lbl = ("Rate limit" if ("rate_limit" in _err_str.lower() or "429" in _err_str)
                            else "Fetch error" if "get_contents" in _err_str else "Error")
                _all_scores.append({
                    "Title": _hint, "Company": "",
                    "IC": 0, "LS": 0, "Best": f"⚠️ {_err_lbl}", "Score": 0,
                    "URL": _u, "Gaps": _err_str[:300],
                })

            _progress_bar.progress((_i + 1) / len(_url_list))
            _df_ul = (pd.DataFrame(_all_scores)
                      .sort_values("Score", ascending=False).reset_index(drop=True))
            _has_err_ul = _df_ul["Best"].astype(str).str.startswith("⚠️").any()
            _cols_ul = ["Title", "Company", "IC", "LS", "Best", "Score", "URL"]
            if _has_err_ul:
                _cols_ul += ["Gaps"]
            _cfg_ul = {
                "IC":    st.column_config.ProgressColumn("IC",  min_value=0, max_value=100, format="%d"),
                "LS":    st.column_config.ProgressColumn("LS",  min_value=0, max_value=100, format="%d"),
                "Score": st.column_config.ProgressColumn("Top", min_value=0, max_value=100, format="%d"),
                "URL":   st.column_config.LinkColumn("URL", display_text="🔗 Link"),
            }
            if _has_err_ul:
                _cfg_ul["Gaps"] = st.column_config.TextColumn(
                    "Error / Gaps", width="large")
            with _live_table.container():
                st.dataframe(_df_ul[_cols_ul], use_container_width=True,
                             hide_index=True, column_config=_cfg_ul)

        _status_txt.markdown(f"✅ Scored {len(_all_scores)} job(s)")
        if _ul_expired:
            st.caption(f"🗓️ Skipped {_ul_expired} expired/closed posting(s).")
        if _all_scores:
            _best_ul = max(_all_scores, key=lambda x: x["Score"])
            st.success(
                f"🏆 Best match: **{_best_ul['Company']} — {_best_ul['Title']}** "
                f"(Score: {_best_ul['Score']}/100)")
            if _best_ul["URL"]:
                st.markdown(f"🔗 [View job]({_best_ul['URL']})")
            with st.expander("📋 Gaps for top pick"):
                st.markdown(_best_ul["Gaps"] or "_None identified_")
        else:
            st.warning(
                "No live jobs scored — links may have been expired/closed or "
                "unreadable. Check the error column above.")

    elif run_btn:
        if not (job_url or pasted_text):
            st.warning(
                "Please provide a job URL or paste the JD text.")
            st.stop()

        from agents.graph import graph
        from report import ATS_PDF_PATH

        initial_state = {
            "job_url":          job_url,
            "search_query":     "",
            "portal":           "Any",
            "skip_cover":       True,
            "raw_jd":           pasted_text,
            "parsed_jd":        None,
            "ic_score":         None,
            "leadership_score": None,
            "best_profile":     None,
            "strengths":        [],
            "gaps":             [],
            "levers":           [],
            "cover_letter":     "",
            "ats_entry":        "",
            "job_source_url":   "",
            "messages":         [],
        }

        progress_placeholder = st.empty()
        steps_log = []

        with st.spinner("🔄 Running agent pipeline..."):
            merged = {**initial_state}
            for step in graph.stream(initial_state, stream_mode="updates"):
                node_name = list(step.keys())[0]
                update = list(step.values())[0]
                merged.update(update)
                msgs = update.get("messages", [])
                if msgs:
                    steps_log.append(f"**[{node_name}]** {msgs[-1].content}")
                    with progress_placeholder.container():
                        for log in steps_log:
                            st.markdown(f"✅ {log}")

        progress_placeholder.empty()

        parsed = merged.get("parsed_jd") or {}
        st.success(
            f"✅ Done — {parsed.get('title', '')} at {parsed.get('company', '')}")
        source_url = merged.get("job_source_url", "")
        if source_url:
            st.caption(f"📎 Source: [{source_url}]({source_url})")

        c1, c2, c3 = st.columns(3)
        ic_score = merged.get("ic_score") or 0
        ld_score = merged.get("leadership_score") or 0
        best = merged.get("best_profile", "IC")
        with c1:
            st.metric("IC Profile",
                      f"{ic_score}/100", delta="Best ✅" if best == "IC" else None)
        with c2:
            st.metric("Leadership Profile", f"{ld_score}/100",
                      delta="Best ✅" if best == "Leadership" else None)
        with c3:
            st.metric("Recommended Profile", best)

        st.divider()

        g_col, l_col = st.columns(2)
        with g_col:
            st.subheader("❌ Gaps")
            for gap in merged.get("gaps", []):
                st.markdown(f"- {gap}")
        with l_col:
            st.subheader("💡 Levers")
            for lever in merged.get("levers", []):
                st.markdown(f"- {lever}")

        st.divider()
        st.subheader("📝 ATS Entry (markdown)")
        st.code(merged.get("ats_entry", ""), language="markdown")

        if ATS_PDF_PATH.exists():
            st.download_button(
                "⬇️ Download ATS Report PDF (all runs)",
                data=ATS_PDF_PATH.read_bytes(),
                file_name="ATS-Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with st.expander("🔍 Full agent output (JSON)"):
            st.json({k: v for k, v in merged.items() if k != "messages"})


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Reports
# ═══════════════════════════════════════════════════════════════════════════════
with tab_report:
    from report import load_runs, save_runs, build_report_pdf, ATS_PDF_PATH, ATS_LOG_PATH

    st.title("📊 ATS Score Report")

    # Profile source confirmation
    with st.expander("📄 Profiles used for ATS scoring", expanded=True):
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("**IC Profile**")
            st.code(str(_IC_PATH), language="text")
            if _IC_PATH.exists():
                st.success("✅ File found")
                with st.expander("Preview (first 500 chars)"):
                    st.text(_IC_PATH.read_text(encoding="utf-8")[:500])
            else:
                st.error("❌ File NOT found — check IC_PROFILE_PATH in .env")
        with pc2:
            st.markdown("**Leadership Profile**")
            st.code(str(_LS_PATH), language="text")
            if _LS_PATH.exists():
                st.success("✅ File found")
                with st.expander("Preview (first 500 chars)"):
                    st.text(_LS_PATH.read_text(encoding="utf-8")[:500])
            else:
                st.error(
                    "❌ File NOT found — check LEADERSHIP_PROFILE_PATH in .env")

    st.divider()

    runs = load_runs()

    if not runs:
        st.info(
            "No runs recorded yet. Run the agent on the **🤖 Agent** tab to start building your report.")
    else:
        # ── Controls bar ──────────────────────────────────────────────────────
        _applied_count = sum(1 for r in runs if r.get("applied", False))
        _ctl1, _ctl2, _ctl3 = st.columns([2, 2, 4])
        with _ctl1:
            if st.button(
                f"🗑️ Clean up applied ({_applied_count})",
                disabled=(_applied_count == 0),
                help="Remove all runs marked as Applied from the log.",
            ):
                _kept = [r for r in runs if not r.get("applied", False)]
                save_runs(_kept)
                if _kept:
                    build_report_pdf(_kept)
                elif ATS_PDF_PATH.exists():
                    ATS_PDF_PATH.unlink()
                st.success(f"Removed {_applied_count} applied run(s).")
                st.rerun()
        with _ctl2:
            if st.button("🗑️ Clear all runs", help="Delete every run from the log."):
                save_runs([])
                if ATS_PDF_PATH.exists():
                    ATS_PDF_PATH.unlink()
                st.success("All runs cleared.")
                st.rerun()

        st.subheader(f"All runs ({len(runs)})", anchor=False)

        rows = []
        for r in reversed(runs):
            best = r.get("best_profile", "IC")
            ic = r.get("ic_score", 0)
            ls = r.get("leadership_score", 0)
            _raw_url = r.get("url", "") or ""
            rows.append({
                "Applied":   "✅" if r.get("applied", False) else "",
                "Date":      r.get("run_date", "")[:16],
                "Company":   r.get("company", ""),
                "Role":      r.get("title", ""),
                "Search":    r.get("search_query", "") if not _raw_url.startswith("http") else "",
                "URL":       _raw_url if _raw_url.startswith("http") else "",
                "IC":        ic,
                "LS":        ls,
                "Best":      best,
                "Top Score": ic if best == "IC" else ls,
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "IC":        st.column_config.ProgressColumn("IC",  min_value=0, max_value=100, format="%d"),
                "LS":        st.column_config.ProgressColumn("LS",  min_value=0, max_value=100, format="%d"),
                "Applied":   st.column_config.TextColumn("Applied", width="small"),
                "Top Score": st.column_config.ProgressColumn("Top", min_value=0, max_value=100, format="%d"),
                "URL":       st.column_config.LinkColumn("URL", display_text="🔗 Link"),
                "Search":    st.column_config.TextColumn("Search Query"),
            },
        )

        st.divider()
        st.subheader("Run details")

        for _ri, r in enumerate(reversed(runs)):
            _real_idx = len(runs) - 1 - _ri   # index in original list
            # always unique
            _run_key = f"{_real_idx}_{r.get('run_date', _real_idx)}"

            best = r.get("best_profile", "IC")
            ic, ls = r.get("ic_score", 0), r.get("leadership_score", 0)
            top = ic if best == "IC" else ls
            company = r.get("company", "")
            title = r.get("title", "")
            _url_raw = r.get("url", "") or ""
            url = _url_raw if _url_raw.startswith("http") else ""
            sq = r.get("search_query", "")
            date = r.get("run_date", "")[:16]
            _is_applied = r.get("applied", False)
            colour = "🟢" if top >= 85 else "🟡" if top >= 70 else "🔴"
            _applied_badge = "  ✅ Applied" if _is_applied else ""

            with st.expander(
                f"{colour} {company} — {title}  ·  IC {ic} / LS {ls} → **{best}**  ·  {date}{_applied_badge}"
            ):
                # ── Applied checkbox + Delete button ──────────────────────────
                _chk_col, _del_col = st.columns([5, 1])
                with _chk_col:
                    _new_applied = st.checkbox(
                        "✅ Mark as Applied",
                        value=_is_applied,
                        key=f"applied_{_run_key}",
                    )
                    if _new_applied != _is_applied:
                        runs[_real_idx]["applied"] = _new_applied
                        save_runs(runs)
                        st.rerun()
                with _del_col:
                    if st.button("🗑️ Delete", key=f"del_{_run_key}",
                                 help="Remove this run from the log"):
                        runs.pop(_real_idx)
                        save_runs(runs)
                        if runs:
                            build_report_pdf(runs)
                        elif ATS_PDF_PATH.exists():
                            ATS_PDF_PATH.unlink()
                        st.rerun()

                st.divider()

                if url:
                    st.markdown(f"🔗 [{url}]({url})")
                elif sq:
                    st.caption(f"🔍 Search query: `{sq}`")

                d1, d2, d3 = st.columns(3)
                d1.metric("IC Score",    f"{ic}/100",
                          delta="Best ✅" if best == "IC" else None)
                d2.metric(
                    "LS Score",    f"{ls}/100", delta="Best ✅" if best == "Leadership" else None)
                d3.metric("Recommended", best)

                gc, lc = st.columns(2)
                with gc:
                    st.markdown("**❌ Gaps**")
                    for g in r.get("gaps", []):
                        st.markdown(f"- {g}")
                with lc:
                    st.markdown("**💡 Levers**")
                    for lv in r.get("levers", []):
                        st.markdown(f"- {lv}")

        st.divider()
        st.subheader("📥 Downloads")
        col_pdf, col_json = st.columns(2)
        with col_pdf:
            if ATS_PDF_PATH.exists():
                st.download_button(
                    "⬇️ ATS-Report.pdf  (all runs, formatted)",
                    data=ATS_PDF_PATH.read_bytes(),
                    file_name="ATS-Report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.info("PDF will appear after the first agent run.")
        with col_json:
            if ATS_LOG_PATH.exists():
                st.download_button(
                    "⬇️ ats_log.json  (raw data)",
                    data=ATS_LOG_PATH.read_bytes(),
                    file_name="ats_log.json",
                    mime="application/json",
                    use_container_width=True,
                )
