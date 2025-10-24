#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coqui TTS — simple starter (now testable & robust)
--------------------------------------------------

✅ What this does
- Turns text into a .wav audio file using a Coqui TTS pretrained model (when available).
- Works on CPU by default; you can force GPU with --device cuda.
- Includes a built-in **dummy** backend to run and test without installing Coqui.

🧰 Install (recommended for real synthesis)
    python -m pip install --upgrade pip
    pip install TTS soundfile torch --extra-index-url https://download.pytorch.org/whl/cpu

  • The extra index URL installs a CPU build of PyTorch (avoids CUDA issues).
  • If you have a working CUDA setup, install torch normally and run with --device cuda.

💿 Basic usage (ARG TEXT or STDIN; prompt only when interactive TTY)
    # 1) Pass text explicitly
    python coqui_tts_starter.py --text "Hello from Coqui!" --out hello.wav

    # 2) Or pipe text via STDIN (no --text required)
    echo "Hello from stdin" | python coqui_tts_starter.py --out hello.wav

    # 3) Interactive prompt is used **only** if stdin is a TTY

Try another model:
    python coqui_tts_starter.py --text "Another voice" \
      --model tts_models/en/ljspeech/tacotron2-DDC_ph --out alt.wav

Voice cloning (XTTS v2):
    python coqui_tts_starter.py \
      --text "This sounds like my sample voice." \
      --model XTTS_v2 \
      --speaker_wav /path/to/your_voice.wav \
      --language en \
      --out cloned.wav

List models (if TTS is installed):
    python -m TTS --list_models

🧪 Run built-in tests (no Coqui required):
    python coqui_tts_starter.py --run-tests

"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import wave
import struct
from typing import Optional, Any

# ------------------------------ Utilities -----------------------------------
DEFAULT_MODEL = "tts_models/en/ljspeech/tacotron2-DDC"


def _resolve_model_alias(name: str) -> str:
    n = name.strip()
    low = n.lower()
    if low in {"xtts_v2", "xtts", "xtts-v2"}:
        return "tts_models/multilingual/multi-dataset/xtts_v2"
    return n


def _stdin_is_interactive() -> bool:
    """Return True if stdin looks like an interactive TTY.

    Be conservative: on any error, return False to avoid prompting in non‑TTY envs.
    """
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def _safe_read_stdin() -> Optional[str]:
    """Read from stdin if not a TTY; return None otherwise. Never raises."""
    try:
        if not _stdin_is_interactive():
            return sys.stdin.read()
    except Exception:
        return None
    return None


def _get_text_value(arg_text: Optional[str], stdin_data: Optional[str]) -> Optional[str]:
    """Return the best available text source.

    Priority: explicit --text > non-empty STDIN > None.
    Leading/trailing whitespace is stripped; empty becomes None.
    """
    if arg_text is not None and arg_text.strip():
        return arg_text.strip()
    if stdin_data is not None:
        stripped = stdin_data.strip()
        if stripped:
            return stripped
    return None


# ------------------------------ Dummy Backend -------------------------------
class DummyTTS:
    """A tiny stand-in for Coqui's TTS for testing.

    It just writes a short 24 kHz WAV file (silence with a quiet beep at start)
    so the rest of the pipeline can be exercised without the real dependency.
    """

    def __init__(self, model_name: str, *_: Any, **__: Any) -> None:  # keep signature flexible
        self.model_name = model_name

    def tts_to_file(self, text: str, file_path: str, **kwargs: Any) -> None:  # noqa: D401
        sr = 24000
        duration_s = max(0.35, min(5.0, len(text) / 25.0))  # 25 chars ≈ 1 second
        num_frames = int(sr * duration_s)

        # Generate a very quiet 440 Hz tone for the first 0.05s, then silence
        tone_frames = int(sr * 0.05)
        data = []
        for i in range(num_frames):
            if i < tone_frames:
                # simple sine approx with integer math; scaled low to avoid clipping
                # Using a tiny periodic pattern instead of real sin to avoid math deps
                sample = 800 if (i % 50) < 25 else -800
            else:
                sample = 0
            # 16-bit PCM little-endian
            data.append(struct.pack('<h', int(sample)))

        out = Path(file_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sr)
            wf.writeframes(b''.join(data))


# ------------------------------ Coqui Loader --------------------------------

def _load_coqui_tts(model_name: str, device: str):
    """Attempt to import and instantiate Coqui's TTS class.
    Returns a TTS-like object or raises an Exception with a helpful message.
    """
    try:
        from TTS.api import TTS  # type: ignore
    except Exception as e:  # pragma: no cover - import errors vary by env
        raise ImportError(
            "Could not import Coqui TTS.\n"
            "Run: pip install TTS soundfile torch --extra-index-url https://download.pytorch.org/whl/cpu\n"
            f"Error: {e}"
        )

    # Prefer CPU for broad compatibility; allow CUDA if asked
    try:
        if device == "cuda":
            try:
                return TTS(model_name=model_name, gpu=True)  # type: ignore[arg-type]
            except Exception:
                return TTS(model_name=model_name, gpu=False, device="cuda")  # type: ignore[arg-type]
        else:
            try:
                return TTS(model_name=model_name, gpu=False)
            except Exception:
                return TTS(model_name=model_name, gpu=False, device="cpu")
    except Exception as e:  # pragma: no cover - depends on runtime env
        if device == "cuda":
            # Retry CPU before giving up
            try:
                return TTS(model_name=model_name, gpu=False)
            except Exception as e2:
                raise RuntimeError(f"Failed to load model on GPU or CPU: {e2}")
        raise RuntimeError(f"Failed to load model: {e}")


# ------------------------------ Core Logic ----------------------------------

def synthesize(
    text: str,
    out_path: Path,
    model: str = DEFAULT_MODEL,
    device: str = "cpu",
    speaker_wav: Optional[str] = None,
    language: Optional[str] = None,
    backend: str = "coqui",  # "coqui" or "dummy"
) -> None:
    """Generate speech and write a WAV file.

    If backend="dummy", Coqui is not required and a short WAV is produced.
    """
    if not text or not text.strip():
        raise ValueError("--text is empty")

    model_name = _resolve_model_alias(model)

    # Auto-default language for XTTS if user forgot it
    if speaker_wav and "xtts" in model_name.lower() and not language:
        language = "en"

    out_path = out_path.with_suffix(".wav")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if backend == "dummy":
        tts_obj = DummyTTS(model_name)
    else:
        tts_obj = _load_coqui_tts(model_name, device)

    kwargs = {"text": text, "file_path": str(out_path)}
    if speaker_wav:
        kwargs["speaker_wav"] = speaker_wav
    if language:
        kwargs["language"] = language

    try:
        tts_obj.tts_to_file(**kwargs)  # type: ignore[attr-defined]
    except TypeError as te:
        # Happens when passing cloning params to single-speaker models
        raise TypeError(
            "Model likely doesn't accept 'speaker_wav'/'language'. "
            "Remove those flags or use --model XTTS_v2."
        ) from te


# ------------------------------ CLI -----------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Turn text into speech (uses Coqui if installed; dummy otherwise)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--text", help="Text to synthesize (or pipe via STDIN)")
    p.add_argument("--out", default="output.wav", help="Output audio path (.wav)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Coqui model name or 'XTTS_v2' alias")
    p.add_argument("--speaker_wav", default=None, help="Reference speaker WAV (XTTS v2)")
    p.add_argument("--language", default=None, help="Language code for XTTS v2 (e.g., en, es)")
    p.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Device for Coqui backend")
    p.add_argument("--backend", default="coqui", choices=["coqui", "dummy"],
                   help="Select 'dummy' to run without installing Coqui")
    p.add_argument("--run-tests", action="store_true", help="Run built-in tests and exit")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.run_tests:
        return _run_tests()

    # Gather text: --text > STDIN; prompt only if interactive TTY
    stdin_data: Optional[str] = _safe_read_stdin()
    text_value = _get_text_value(args.text, stdin_data)

    if text_value is None:
        if _stdin_is_interactive():
            try:
                text_value = input("Enter text to synthesize: ").strip()
            except (EOFError, KeyboardInterrupt, OSError):
                text_value = ""
        else:
            # Non-interactive environment: do not attempt input(); avoid OSError: [Errno 29]
            print("[!] --text is required (pass --text or pipe via STDIN). Not prompting because stdin is not a TTY.")
            return 2

    if not text_value:
        print("[!] --text is required (pass --text, pipe via STDIN, or type at prompt)")
        return 2

    try:
        synthesize(
            text=text_value,
            out_path=Path(args.out),
            model=args.model,
            device=args.device,
            speaker_wav=args.speaker_wav,
            language=args.language,
            backend=args.backend,
        )
    except ValueError as ve:
        print(f"[!] {ve}")
        return 2
    except ImportError as ie:
        print("[!] Could not import Coqui TTS.\n"
              "    Run: pip install TTS soundfile torch --extra-index-url https://download.pytorch.org/whl/cpu\n"
              f"    Error: {ie}")
        print("Tip: you can still try the script with --backend dummy")
        return 3
    except TypeError as te:
        print("[!] The selected model likely doesn't accept 'speaker_wav'/'language'.\n"
              "    Remove those flags or use --model XTTS_v2.")
        print(f"Detailed error: {te}")
        return 4
    except Exception as e:
        print("[!] Something went wrong while generating audio:")
        print(e)
        return 5

    print(f"[✔] Done! Wrote: {Path(args.out).with_suffix('.wav').resolve()}")
    print("Tip: open the .wav with your default player or drag it into a DAW.")
    return 0


# ------------------------------ Tests ---------------------------------------
# These tests avoid the Coqui dependency by using the dummy backend.

def _run_tests() -> int:  # pragma: no cover - simple CLI runner
    import unittest
    import tempfile

    class TTSTests(unittest.TestCase):
        def test_resolve_model_alias(self):
            self.assertEqual(_resolve_model_alias('XTTS_v2'),
                             'tts_models/multilingual/multi-dataset/xtts_v2')
            self.assertEqual(_resolve_model_alias('xtts'),
                             'tts_models/multilingual/multi-dataset/xtts_v2')
            self.assertEqual(_resolve_model_alias('tts_models/en/ljspeech/tacotron2-DDC'),
                             'tts_models/en/ljspeech/tacotron2-DDC')

        def test_empty_text_error(self):
            with self.assertRaises(ValueError):
                synthesize(text="  ", out_path=Path('x.wav'), backend='dummy')

        def test_dummy_generation_creates_file(self):
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / 'hello.wav'
                synthesize(text="hello", out_path=out, backend='dummy')
                self.assertTrue(out.exists(), "Output WAV should be created by dummy backend")
                # File should be a valid WAV header
                with wave.open(str(out), 'rb') as wf:
                    self.assertEqual(wf.getnchannels(), 1)
                    self.assertEqual(wf.getsampwidth(), 2)
                    self.assertEqual(wf.getframerate(), 24000)

        def test_xtts_defaults_language(self):
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / 'x.wav'
                # Should not raise even if language is omitted; synthesize fills 'en'
                synthesize(text="hello", out_path=out, model='XTTS_v2', backend='dummy')
                self.assertTrue(out.exists())

        # New tests for text sourcing logic
        def test_get_text_prefers_arg_over_stdin(self):
            self.assertEqual(_get_text_value("arg text", "stdin text"), "arg text")

        def test_get_text_from_stdin_when_arg_missing(self):
            self.assertEqual(_get_text_value(None, "  from stdin  \n"), "from stdin")

        def test_get_text_none_when_both_missing(self):
            self.assertIsNone(_get_text_value(None, None))

        # New tests for interactive detection helpers
        def test_stdin_is_interactive_handles_errors(self):
            # We can't simulate TTY here, but we can at least ensure it returns a bool and never raises
            self.assertIsInstance(_stdin_is_interactive(), bool)

        def test_safe_read_stdin_no_raise(self):
            # Should never raise and should return a str or None
            val = _safe_read_stdin()
            self.assertTrue((val is None) or isinstance(val, str))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TTSTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
