from pathlib import Path
import tempfile

import streamlit as st

from core.portfolio_risk_dashboard import PortfolioRiskDashboard
from core.database import DatabaseManager
from core.position_sizer import PositionSizer
from core.order_preview import OrderPreviewBuilder
from core.paper_trade_simulator import PaperTradeSimulator

from ticker_detector import TickerDetector
from live_transcription import LiveTranscriptionEngine, WhisperCppBackend
from live_audio_capture import LiveAudioCapture
from live_worker import TraderTVLiveWorker
from live_scanner import LiveScannerService


WHISPER_EXE = Path(
    r"C:\Users\DELL\Desktop\whisper.cpp\build\bin\Release\whisper-cli.exe"
)

WHISPER_MODEL = Path(
    r"C:\Users\DELL\Desktop\whisper.cpp\ggml-tiny.en.bin"
)

WATCHLIST = [
    "NVDA", "AMD", "AAPL", "TSLA", "PLTR", "META",
    "MSFT", "AMZN", "NFLX", "AVGO", "SMCI",
]


def get_detector() -> TickerDetector:
    return TickerDetector(WATCHLIST)


def get_transcription_engine() -> LiveTranscriptionEngine:
    backend = WhisperCppBackend(
        str(WHISPER_EXE),
        str(WHISPER_MODEL),
    )
    return LiveTranscriptionEngine(backend)


def analyze_live_chunk() -> tuple[str, list[str]]:
    capture = LiveAudioCapture(
        device=None,
        samplerate=48000,
        channels=2,
        chunk_seconds=10,
    )
    audio_path = None

    try:
        audio_path = capture.record_chunk()
        result = get_transcription_engine().transcribe_file(
            str(audio_path)
        )
        transcript = result.text
        detected = get_detector().detect(transcript)
        return transcript, detected
    finally:
        if audio_path is not None:
            capture.cleanup(audio_path)


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

    @st.cache_resource
    def get_live_scanner() -> LiveScannerService:
        return LiveScannerService()

    if "scanner_results" not in st.session_state:
        st.session_state.scanner_results = []

    risk_dashboard = PortfolioRiskDashboard(DatabaseManager())
    position_sizer = PositionSizer()
    order_preview_builder = OrderPreviewBuilder()
    paper_simulator = PaperTradeSimulator(DatabaseManager())

    @st.fragment(run_every=1)
    def render_scanner_results() -> None:
        if not st.session_state.scanner_results:
            st.info("Waiting for a TraderTV ticker mention...")
            return

        for result in st.session_state.scanner_results:
            symbol = result["Symbol"]
            decision = result["Decision"]

            st.markdown(f"### {symbol} — {decision}")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Price", f"${result['Price']:.2f}")
            c2.metric("Score", f"{result['Score']}/100")
            c3.metric("Confidence", f"{result['Confidence']}%")
            c4.metric("Market", result["Market"])

            st.caption(
                f"Quality: {result['Quality']} | "
                f"TraderTV detected: {'Yes' if result['TraderTV'] else 'No'}"
            )

            st.markdown("**Technical**")
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("MA19", result["MA19"])
            t2.metric("MA38", result["MA38"])
            t3.metric("MA209", result["MA209"])
            t4.metric("ADX", result["ADX"])

            t5, t6, t7, t8 = st.columns(4)
            t5.metric("DI+", result["DI+"])
            t6.metric("DI-", result["DI-"])
            t7.metric("RVOL", result["RVOL"])
            t8.metric("Volume", f"{result['Volume']:,}")

            st.markdown("**Trade Plan**")
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Entry", f"${result['Entry']:.2f}")
            p2.metric("Stop", f"${result['Stop']:.2f}")
            p3.metric("Target", f"${result['Target']:.2f}")
            p4.metric("R:R", result["RR"])

            st.markdown("**Position Sizing**")
            sizing = position_sizer.calculate(
                result["Entry"],
                result["Stop"],
                risk_dashboard.get_summary(),
            )

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Shares", sizing["Shares"])
            s2.metric("Position Value", f"${sizing['PositionValue']:.2f}")
            s3.metric("Position Risk", f"${sizing['PositionRisk']:.2f}")
            sizing_status = (
                "ELIGIBLE" if sizing["Eligible"] else "BLOCKED"
            )
            s4.metric("Risk Gate", sizing_status)

            execution_allowed = (
                decision == "BUY" and sizing["Eligible"]
            )
            if execution_allowed:
                st.success("Execution Gate: READY")
            else:
                st.error("Execution Gate: BLOCKED")

            if sizing["SizingReasons"]:
                st.warning(sizing["SizingReasons"])

            preview = order_preview_builder.build(result, sizing)
            st.markdown("**Order Preview**")
            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Side", preview["Side"])
            o2.metric("Shares", preview["Shares"])
            o3.metric("Total Risk", f"${preview['TotalRisk']:.2f}")
            o4.metric("Mode", preview["Mode"])

            if preview["Ready"]:
                st.success("Order Preview: READY")
                if st.button(
                    f"Open Paper Trade — {symbol}",
                    key=f"paper_trade_{symbol}",
                    type="primary",
                ):
                    paper_result = paper_simulator.execute(preview)
                    if paper_result["Executed"]:
                        st.success(
                            f"Paper position opened: {symbol} "
                            f"{paper_result['Shares']} share(s) "
                            f"@ ${paper_result['Entry']:.2f}"
                        )
                    else:
                        st.warning(paper_result["Reason"])
            else:
                st.info("Order Preview: BLOCKED — preview only")

            st.markdown(f"**Why {decision}?**")
            if result.get("DecisionReasons"):
                st.warning(result["DecisionReasons"])
            else:
                st.caption("No decision explanation returned.")

            st.markdown("**Score Contributors**")
            if result["Reasons"]:
                st.write(result["Reasons"])
            else:
                st.caption("No scoring reasons returned.")

            with st.expander("Technical Details"):
                st.dataframe([result], width="stretch")

            st.divider()

    render_scanner_results()

    st.subheader("Portfolio Risk")

    dashboard = PortfolioRiskDashboard(DatabaseManager())
    summary = dashboard.get_summary()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Capital",
        f"${summary['account_capital']:.2f}",
    )
    c2.metric(
        "Available Cash",
        f"${summary['available_cash']:.2f}",
    )
    c3.metric(
        "Portfolio Risk",
        f"${summary['current_portfolio_risk']:.2f}"
        f" / ${summary['max_portfolio_risk']:.2f}",
    )
    c4.metric(
        "Open Positions",
        f"{summary['open_positions']}"
        f" / {summary['max_open_positions']}",
    )

    if summary["positions"]:
        st.dataframe(
            summary["positions"],
            width="stretch",
        )
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
            allow="accelerometer; autoplay; clipboard-write;
                   encrypted-media; gyroscope;
                   picture-in-picture; web-share"
            allowfullscreen>
        </iframe>
        """,
        unsafe_allow_html=True,
    )

    st.caption("TraderTV Live broadcast player")
    st.subheader("Live Transcript")

    if "live_transcript" not in st.session_state:
        st.session_state.live_transcript = ""

    if "live_tickers" not in st.session_state:
        st.session_state.live_tickers = []

    if "live_error" not in st.session_state:
        st.session_state.live_error = ""

    @st.cache_resource
    def get_live_worker() -> TraderTVLiveWorker:
        return TraderTVLiveWorker(
            whisper_exe=str(WHISPER_EXE),
            whisper_model=str(WHISPER_MODEL),
            symbols=WATCHLIST,
            chunk_seconds=10,
        )

    live_worker = get_live_worker()

    if not WHISPER_EXE.is_file():
        st.error(f"whisper-cli.exe not found: {WHISPER_EXE}")
    elif not WHISPER_MODEL.is_file():
        st.error(f"Whisper model not found: {WHISPER_MODEL}")
    else:
        start_col, stop_col = st.columns(2)

        with start_col:
            if st.button(
                "Start Live",
                type="primary",
                width="stretch",
                disabled=live_worker.running,
            ):
                st.session_state.live_error = ""
                live_worker.start()
                st.rerun()

        with stop_col:
            if st.button(
                "Stop Live",
                width="stretch",
                disabled=not live_worker.running,
            ):
                live_worker.stop()
                st.rerun()

        if live_worker.running:
            st.success(
                "LIVE: listening to TraderTV in 10-second chunks."
            )
        else:
            st.caption("Live listener is stopped.")

        @st.fragment(run_every=1)
        def render_live_updates() -> None:
            update = live_worker.latest_update()

            if update is not None:
                if update.error:
                    st.session_state.live_error = update.error
                else:
                    st.session_state.live_error = ""
                    st.session_state.live_transcript = (
                        update.transcript
                    )
                    st.session_state.live_tickers = list(
                        update.tickers
                    )

                    if update.tickers:
                        try:
                            st.session_state.scanner_results = (
                                get_live_scanner().scan_symbols(
                                    list(update.tickers)
                                )
                            )
                        except Exception as exc:
                            st.session_state.live_error = (
                                "Scanner failed: " + str(exc)
                            )

            if st.session_state.live_error:
                st.error(
                    "Live capture failed: "
                    + st.session_state.live_error
                )

            if st.session_state.live_transcript:
                st.text_area(
                    "Latest live transcript",
                    value=st.session_state.live_transcript,
                    height=140,
                    disabled=True,
                    key="continuous_live_transcript",
                )

                if st.session_state.live_tickers:
                    st.success(
                        "Live detected tickers: "
                        + ", ".join(
                            st.session_state.live_tickers
                        )
                    )
                else:
                    st.info(
                        "No tracked ticker detected "
                        "in the latest live chunk."
                    )

        render_live_updates()

    if (
        not WHISPER_EXE.is_file()
        or not WHISPER_MODEL.is_file()
    ) and st.session_state.live_transcript:
        st.text_area(
            "Latest live transcript",
            value=st.session_state.live_transcript,
            height=140,
            disabled=True,
        )

        if st.session_state.live_tickers:
            st.success(
                "Live detected tickers: "
                + ", ".join(st.session_state.live_tickers)
            )
        else:
            st.info(
                "No tracked ticker detected "
                "in the latest live chunk."
            )

    with st.expander("Audio file test / manual transcription"):
        audio_file = st.file_uploader(
            "Upload audio for Whisper transcription",
            type=["wav", "mp3", "ogg", "flac"],
        )

        if audio_file is not None:
            suffix = Path(audio_file.name).suffix

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temp_audio:
                temp_audio.write(audio_file.getbuffer())
                temp_audio_path = temp_audio.name

            try:
                engine = get_transcription_engine()

                with st.spinner(
                    "Transcribing audio with whisper.cpp..."
                ):
                    result = engine.transcribe_file(
                        temp_audio_path
                    )

                transcript = result.text

                st.text_area(
                    "Whisper transcript",
                    value=transcript,
                    height=140,
                )

                detected = get_detector().detect(transcript)

                if detected:
                    st.success(
                        "Detected tickers: "
                        + ", ".join(detected)
                    )
                else:
                    st.info(
                        "No tracked ticker detected "
                        "in transcript."
                    )

            except Exception as exc:
                st.error(f"Transcription failed: {exc}")

            finally:
                try:
                    Path(temp_audio_path).unlink(
                        missing_ok=True
                    )
                except OSError:
                    pass
