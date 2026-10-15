"""Optional Streamlit dashboard for the File Integrity Monitoring System."""
from pathlib import Path
import streamlit as st
import pandas as pd

from fim_core import create_baseline, scan_folder, load_report, BASELINE_PATH, REPORTS_DIR

st.set_page_config(page_title="File Integrity Monitor", page_icon="🛡️", layout="wide")
st.title("🛡️ File Integrity Monitoring System")
st.caption("SHA-256 based detection of modified, new, and deleted files")

with st.sidebar:
    st.header("Monitor a folder")
    folder = st.text_input("Folder path", value=str((Path(__file__).resolve().parent / "sample_data" / "monitored_folder")))
    st.caption("Use a folder you own or are authorized to monitor.")
    if st.button("Create / Replace Baseline", use_container_width=True):
        try:
            result = create_baseline(folder)
            st.session_state["message"] = f"Baseline created: {result['file_count']} file(s)."
            st.session_state["message_type"] = "success"
        except Exception as exc:
            st.session_state["message"] = str(exc)
            st.session_state["message_type"] = "error"
    if st.button("Scan for Changes", use_container_width=True):
        try:
            result = scan_folder(folder)
            st.session_state["latest_report"] = result
            st.session_state["message"] = result["summary"]["status"]
            st.session_state["message_type"] = "success" if result["summary"]["status"] == "NO CHANGES" else "warning"
        except Exception as exc:
            st.session_state["message"] = str(exc)
            st.session_state["message_type"] = "error"

if st.session_state.get("message"):
    kind = st.session_state.get("message_type", "info")
    getattr(st, kind)(st.session_state["message"])

report = st.session_state.get("latest_report")
if report is None:
    try:
        report = load_report()
    except Exception:
        report = None

if report:
    s = report.get("summary", {})
    a, b, c, d = st.columns(4)
    a.metric("Modified", s.get("modified_count", 0))
    b.metric("New", s.get("new_count", 0))
    c.metric("Deleted", s.get("deleted_count", 0))
    d.metric("Unchanged", s.get("unchanged_count", 0))
    status = s.get("status", "N/A")
    if status == "NO CHANGES":
        st.success(f"Status: {status}")
    else:
        st.warning(f"Status: {status}")
    st.write(f"**Monitored folder:** `{report.get('root_folder', '')}`")
    st.write(f"**Scan time (UTC):** {report.get('scan_time_utc', 'N/A')}")

    for key, title in (("modified", "Modified files"), ("new", "New files"), ("deleted", "Deleted files")):
        with st.expander(f"{title} ({len(report.get(key, []))})", expanded=bool(report.get(key))):
            items = report.get(key, [])
            if items:
                st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
            else:
                st.write("None detected.")
    with st.expander(f"Unchanged files ({len(report.get('unchanged', []))})"):
        if report.get("unchanged"):
            st.dataframe(pd.DataFrame({"path": report["unchanged"]}), use_container_width=True, hide_index=True)
        else:
            st.write("No unchanged files listed.")
    with st.expander(f"Read errors ({len(report.get('errors', []))})"):
        if report.get("errors"):
            st.dataframe(pd.DataFrame(report["errors"]), use_container_width=True, hide_index=True)
        else:
            st.write("No read errors.")
else:
    st.info("Create a baseline from the sidebar, then run a scan. The included sample folder is a good place to start.")

st.divider()
st.caption("Tip: keep the baseline in a protected location. Anyone who can change the baseline may hide changes.")
