import streamlit as st

from core.portfolio_risk_dashboard import PortfolioRiskDashboard
from core.database import DatabaseManager


st.set_page_config(
    page_title="TradingAI-Pro",
    page_icon="📈",
    layout="wide",
)

st.title("TradingAI-Pro Platform")
st.caption("Scanner + Portfolio Risk + TraderTV Live")

left, right = st.columns([1.15, 1])

with left:
    st.subheader("Market Scanner")
    st.info("Scanner integration is the next step.")

    st.subheader("Portfolio Risk")
    dashboard = PortfolioRiskDashboard(DatabaseManager())
    summary = dashboard.get_summary()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capital", f"${summary['account_capital']:.2f}")
    c2.metric("Available Cash", f"${summary['available_cash']:.2f}")
    c3.metric(
        "Portfolio Risk",
        f"${summary['current_portfolio_risk']:.2f}"
        f" / ${summary['max_portfolio_risk']:.2f}",
    )
    c4.metric(
        "Open Positions",
        f"{summary['open_positions']} / {summary['max_open_positions']}",
    )

    if summary["positions"]:
        st.dataframe(summary["positions"], width="stretch")
    else:
        st.write("No open positions.")

with right:
    st.subheader("TraderTV Live")
    st.markdown(
        """
        <iframe
            width="100%"
            height="420"
            src="https://www.youtube.com/embed/kowCxUW-SO0"
            title="TraderTV Live"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen>
        </iframe>
        """,
        unsafe_allow_html=True,
    )

    st.caption("TraderTV Live broadcast player")

    st.subheader("Live Transcript")
    st.info("Live transcription and ticker detection will be added after the base UI is validated.")
