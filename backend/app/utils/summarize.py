# app/utils/summarize.py

import torch
import logging
from transformers import pipeline
from faster_whisper import WhisperModel

logger = logging.getLogger("talkvault.utils.summarize")

# Global caches
_whisper_model = None
_summarizer_pipeline = None


def _get_whisper():
    """Load Whisper model lazily."""
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model (small, CPU)...")
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
        logger.info("Whisper model loaded successfully.")
    return _whisper_model


def _get_summarizer():
    """Load BART summarizer model lazily."""
    global _summarizer_pipeline
    if _summarizer_pipeline is None:
        logger.info("Loading BART summarization model...")
        _summarizer_pipeline = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1  # CPU
        )
        logger.info("Summarization model loaded successfully.")
    return _summarizer_pipeline


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using Whisper.
    """
    try:
        whisper = _get_whisper()
        logger.info(f"Transcribing audio file: {audio_path}")
        segments, _ = whisper.transcribe(audio_path)
        text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
        logger.info(f"Transcription complete — {len(text)} characters.")
        return text
    except Exception as e:
        logger.exception("Error during audio transcription: %s", e)
        raise RuntimeError(f"Transcription failed: {e}")


def summarize_text(text: str, min_length=20, max_length=120) -> str:
    """
    Summarize transcript text using BART.
    """
    try:
        summarizer = _get_summarizer()
        logger.info(f"Summarizing text ({len(text)} chars)...")
        summary = summarizer(
            text,
            min_length=min_length,
            max_length=max_length,
            do_sample=False
        )
        summary_text = summary[0]["summary_text"].strip()
        logger.info(f"Summary generated — {len(summary_text)} characters.")
        return summary_text
    except Exception as e:
        logger.exception("Error during summarization: %s", e)
        raise RuntimeError(f"Summarization failed: {e}")
