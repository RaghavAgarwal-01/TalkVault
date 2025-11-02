import torch
import logging
from transformers import pipeline
from faster_whisper import WhisperModel

logger = logging.getLogger("talkvault.utils.summarize")

# Global caches
_whisper_model = None
_summarizer_pipeline = None


def _get_device():
    """Return GPU if available, else CPU."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"🚀 Using GPU: {gpu_name}")
        return 0  # GPU device index for transformers
    else:
        logger.info("⚙️ Using CPU (no GPU available)")
        return -1


def _get_whisper():
    """Load Whisper model lazily."""
    global _whisper_model
    if _whisper_model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if torch.cuda.is_available() else "int8"
        logger.info(f"Loading Whisper model (small, device={device}, compute_type={compute_type})...")
        _whisper_model = WhisperModel("small", device=device, compute_type=compute_type)
        logger.info("Whisper model loaded successfully.")
    return _whisper_model


def _get_summarizer():
    """Load optimized BART summarizer model lazily."""
    global _summarizer_pipeline
    if _summarizer_pipeline is None:
        device = _get_device()
        logger.info("Loading high-quality summarization model (philschmid/bart-large-cnn-samsum)...")

        # Use FP16 for faster inference on GPU
        dtype = torch.float16 if device == 0 else None

        _summarizer_pipeline = pipeline(
            "summarization",
            model="philschmid/bart-large-cnn-samsum",
            device=device,
            torch_dtype=dtype,
        )
        logger.info("Summarization model loaded successfully.")
    return _summarizer_pipeline


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file to text using Whisper."""
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


def chunk_text(text, max_words=400):
    """Split text into smaller chunks of up to ~max_words words."""
    words = text.split()
    for i in range(0, len(words), max_words):
        yield " ".join(words[i:i + max_words])


def summarize_text(text: str) -> str:
    """
    Summarize large text safely by chunking and merging results.
    GPU-accelerated if available.
    """
    try:
        summarizer = _get_summarizer()
        chunks = list(chunk_text(text))
        summaries = []

        for chunk in chunks:
            result = summarizer(
                chunk,
                max_length=500,
                min_length=150,
                do_sample=False
            )
            summaries.append(result[0]["summary_text"].strip())

        combined_text = " ".join(summaries)
        final_summary = summarizer(
            combined_text,
            max_length=500,
            min_length=150,
            do_sample=False
        )[0]["summary_text"]

        return final_summary.strip()

    except Exception as e:
        logger.exception("Summarization failed: %s", e)
        raise RuntimeError(f"Summarization failed: {e}")
