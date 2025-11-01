"""
Lazy-loading summarizer & transcription service.

Behavior:
- Models are NOT loaded at import time.
- The first request that needs models will trigger a background loader thread.
- Requests will wait for the loader to finish (with a timeout) before running.
- Loading runs in a separate thread so FastAPI/uvicorn startup isn't blocked.
"""

import threading
import time
import logging
from typing import Optional

logger = logging.getLogger("talkvault.summarizer_service")

# Globals for models
_models_lock = threading.Lock()
_models_loaded_event = threading.Event()
_models_loading = False
_models_failed = False

# Model references (populated by loader)
_transcriber = None
_summarizer_model = None
_summarizer_tokenizer = None

# Config - adjust if desired
MODEL_LOAD_TIMEOUT = 300  # seconds to wait for model loading in requests


def _load_models():
    """Internal function that runs in a background thread to load models."""
    global _models_loading, _models_failed
    global _transcriber, _summarizer_model, _summarizer_tokenizer

    try:
        logger.info("🔹 Background: Starting to load transcription & summarization models...")
        # Example: load faster-whisper for transcription (if you use it)
        # Import inside function to avoid heavy imports at module import time.
        try:
            from faster_whisper import WhisperModel
        except Exception as e:
            # faster_whisper not available or import failed
            logger.warning("faster_whisper import failed: %s", e)
            WhisperModel = None

        # Load transcription model (if available)
        if WhisperModel is not None:
            # choose model size appropriate for your machine, e.g. "small" or "base"
            logger.info("Loading Whisper model (faster_whisper)...")
            _transcriber = WhisperModel("small", device="cpu", compute_type="default")
            logger.info("Whisper model loaded.")
        else:
            _transcriber = None
            logger.warning("WhisperModel not available; transcription disabled.")

        # Load summarizer (HuggingFace transformers)
        logger.info("Loading summarizer tokenizer & model (transformers)...")
        from transformers import AutoTokenizer, PegasusForConditionalGeneration

        # Using google/pegasus-xsum here as example — you already had this in logs.
        # You can replace with a smaller/faster model if CPU-bound.
        MODEL_NAME = "google/pegasus-xsum"
        _summarizer_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _summarizer_model = PegasusForConditionalGeneration.from_pretrained(MODEL_NAME)
        logger.info("Summarizer loaded.")

        # mark loaded
        _models_failed = False
        _models_loaded_event.set()
        logger.info("🔹 Background: Models loaded successfully.")
    except Exception as e:
        logger.exception("Failed to load models: %s", e)
        _models_failed = True
        # still set the event so requests don't hang forever
        _models_loaded_event.set()
    finally:
        _models_loading = False


def ensure_models_loading():
    """
    Ensure a background loader is started. Returns immediately.
    If loader already ran (successfully or failed), does nothing.
    """
    global _models_loading

    # Fast path: already loaded or failed
    if _models_loaded_event.is_set():
        return

    with _models_lock:
        if _models_loading or _models_loaded_event.is_set():
            return
        _models_loading = True
        # Start background thread
        thread = threading.Thread(target=_load_models, name="TalkVaultModelLoader", daemon=True)
        thread.start()
        logger.info("Model loader thread started.")


def wait_for_models(timeout: Optional[int] = MODEL_LOAD_TIMEOUT) -> bool:
    """
    Wait up to `timeout` seconds for models to finish loading.
    Returns True if loaded successfully, False if failed or timed out.
    """
    ensure_models_loading()
    logger.info("Waiting for models to finish loading (timeout=%s)...", timeout)
    finished = _models_loaded_event.wait(timeout=timeout)
    if not finished:
        logger.error("Timed out waiting for models to load.")
        return False
    if _models_failed:
        logger.error("Model loader reported failure.")
        return False
    return True


# Public functions that endpoints should call

def transcribe_audio_file(file_path: str, language: Optional[str] = None) -> str:
    """
    Transcribe an audio file. This will block until models are loaded (or fail/timeout).
    Returns the transcript (string) or raises RuntimeError on failure.
    """
    ok = wait_for_models()
    if not ok:
        raise RuntimeError("Models not available for transcription (load failed or timed out).")

    if _transcriber is None:
        raise RuntimeError("Transcription model not configured on this server.")

    # Run transcription (synchronous call to faster_whisper)
    try:
        logger.info("Starting transcription for %s", file_path)
        segments, info = _transcriber.transcribe(file_path, beam_size=5, language=language)
        # collect text
        text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
        logger.info("Transcription finished: %d chars", len(text))
        return text
    except Exception as e:
        logger.exception("Error during transcription: %s", e)
        raise RuntimeError(f"Transcription failed: {e}")


def summarize_text(text: str, max_length: int = 60, min_length: int = 10) -> str:
    """
    Summarize the given text using the summarizer model. Blocks until models loaded.
    Returns a summarized string.
    """
    ok = wait_for_models()
    if not ok:
        raise RuntimeError("Models not available for summarization (load failed or timed out).")

    if _summarizer_model is None or _summarizer_tokenizer is None:
        raise RuntimeError("Summarizer model not configured on this server.")

    try:
        logger.info("Tokenizing input for summarization (input_chars=%d)...", len(text))
        inputs = _summarizer_tokenizer(text, truncation=True, padding="longest", return_tensors="pt")
        # generate
        summary_ids = _summarizer_model.generate(
            inputs["input_ids"],
            num_beams=4,
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            early_stopping=True,
        )
        summary = _summarizer_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        logger.info("Summarization finished (summary_chars=%d).", len(summary))
        return summary
    except Exception as e:
        logger.exception("Error during summarization: %s", e)
        raise RuntimeError(f"Summarization failed: {e}")
