from pathlib import Path
import tempfile

import streamlit as st

from core.portfolio_risk_dashboard import PortfolioRiskDashboard
from core.database import DatabaseManager

from ticker_detector import TickerDetector
from live_transcription import LiveTranscriptionEngine, WhisperCppBackend


WHISPER_EXE = Path(
    r"C:\Users\DELL\Desktop\whisper.cpp\build\bin\Release\whisper-cli.exe"
)

WHISPER_MODEL = Path(
    r"C:\Users\DELL\Desktop\whisper.cpp\ggml-tiny.en.bin"
)


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

    detector = TickerDetector(
        [
            "NVDA",
            "AMD",
            "AAPL",
            "TSLA",
            "PLTR",
            "META",
            "MSFT",
            "AMZN",
            "NFLX",
            "AVGO",
            "SMCI",
        ]
    )

    audio_file = st.file_uploader(
        "Upload audio for Whisper transcription",
        type=["wav", "mp3", "ogg", "flac"],
    )

    if audio_file is not None:

        if not WHISPER_EXE.is_file():
            st.error(
                f"whisper-cli.exe not found: {WHISPER_EXE}"
            )

        elif not WHISPER_MODEL.is_file():
            st.error(
                f"Whisper model not found: {WHISPER_MODEL}"
            )

        else:
            suffix = Path(audio_file.name).suffix

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            ) as temp_audio:

                temp_audio.write(audio_file.getbuffer())
                temp_audio_path = temp_audio.name

            try:
                backend = WhisperCppBackend(
                    str(WHISPER_EXE),
                    str(WHISPER_MODEL),
                )

                engine = LiveTranscriptionEngine(backend)

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

                detected = detector.detect(transcript)

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
                st.error(
                    f"Transcription failed: {exc}"
                )

            finally:
                try:
                    Path(temp_audio_path).unlink(
                        missing_ok=True
                    )
                except OSError:
                    pass