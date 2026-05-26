"""BioDash — Streamlit dashboard."""
import shutil

import streamlit as st

from core.logging_config import setup_logging
from core.paths import CONFIG_EXAMPLE_PATH, CONFIG_PATH, UNIFIED_LOG_PATH
from core.version import __version__
from ui.cache import cached_settings, cached_shifts, cached_weekly_stats, clear_caches, shifts_file_mtime
from ui.dashboard import render_dashboard
from ui.log_shift import render_log_shift
from ui.refuel import render_refuel
from ui.settings_tab import render_settings
from ui.sidebar import render_sidebar_status

setup_logging()

st.set_page_config(page_title=f"BioDash AU | v{__version__}", layout="wide", page_icon="🚀")


def _missing_config_screen() -> None:
    st.error("Missing `config/settings.json` — your private config is not set up.")
    st.markdown(
        f"Copy [`config/settings.example.json`]({CONFIG_EXAMPLE_PATH.name}) "
        "to `config/settings.json`, or click below."
    )
    if st.button("Create settings from example", type="primary"):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(CONFIG_EXAMPLE_PATH, CONFIG_PATH)
        clear_caches()
        st.rerun()
    st.stop()


try:
    settings = cached_settings()
except FileNotFoundError:
    _missing_config_screen()

df = cached_shifts()
stats = cached_weekly_stats(shifts_file_mtime())

render_sidebar_status(settings, stats)

st.title("BioDash AU")
st.caption(f"Delivery driver analytics · v{__version__}")

tab_dash, tab_log, tab_refuel, tab_settings = st.tabs(
    ["Dashboard", "Log shift", "Refuel", "Settings"]
)

with tab_dash:
    if df.empty:
        st.warning(
            f"No shift data in `{UNIFIED_LOG_PATH.name}`. "
            "Log a shift in the **Log shift** tab or run `Log_Shift.bat`."
        )
    else:
        render_dashboard(df, stats)

with tab_log:
    render_log_shift(settings)

with tab_refuel:
    render_refuel(settings)

with tab_settings:
    render_settings(settings)
