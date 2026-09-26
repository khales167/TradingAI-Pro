from pathlib import Path
import tempfile

import streamlit as st

from core.portfolio_risk_dashboard import PortfolioRiskDashboard
from core.database import DatabaseManager

from ticker_detector import TickerDetector
from live_transcription import LiveTranscriptionEngine, WhisperCppBackend
from live_audio_capture import LiveAudioCapture


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
        device=12,
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
    st.info("Scanner integration is the next step.")

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

    if not WHISPER_EXE.is_file():
        st.error(f"whisper-cli.exe not found: {WHISPER_EXE}")
    elif not WHISPER_MODEL.is_file():
        st.error(f"Whisper model not found: {WHISPER_MODEL}")
    else:
        if st.button(
            "Capture & Analyze Live 10s",
            type="primary",
            width="stretch",
        ):
            try:
                with st.spinner(
                    "Listening to TraderTV for 10 seconds..."
                ):
                    transcript, detected = analyze_live_chunk()

                st.session_state.live_transcript = transcript
                st.session_state.live_tickers = detected

            except Exception as exc:
                st.error(f"Live capture failed: {exc}")

    if st.session_state.live_transcript:
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
