"""
Speech utilities for Voice for Livelihood.

ASR:
    AI4Bharat Indic Conformer

TTS:
    AI4Bharat Indic Parler-TTS

Audio loading/resampling:
    SoundFile + SciPy

This avoids torchaudio/TorchCodec for WAV loading on Windows.
"""

import math

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
import torch


LANGUAGES = {
    "Hindi": "hi",
    "Marathi": "mr",
    "Telugu": "te",
    "Tamil": "ta",
    "Bengali": "bn",
    "Gujarati": "gu",
}


TTS_VOICE_DESCRIPTIONS = {
    "hi": (
        "Divya's voice is warm and clear, speaking Hindi at a moderate "
        "pace with a calm, empathetic tone, in a quiet recording with "
        "no background noise."
    ),

    "mr": (
        "A warm, clear female voice speaking Marathi at a moderate "
        "pace with a calm, empathetic tone, in a quiet recording with "
        "no background noise."
    ),

    "te": (
        "A warm, clear female voice speaking Telugu at a moderate "
        "pace with a calm, empathetic tone, in a quiet recording with "
        "no background noise."
    ),

    "ta": (
        "A warm, clear female voice speaking Tamil at a moderate "
        "pace with a calm, empathetic tone, in a quiet recording with "
        "no background noise."
    ),

    "bn": (
        "A warm, clear female voice speaking Bengali at a moderate "
        "pace with a calm, empathetic tone, in a quiet recording with "
        "no background noise."
    ),

    "gu": (
        "A warm, clear female voice speaking Gujarati at a moderate "
        "pace with a calm, empathetic tone, in a quiet recording with "
        "no background noise."
    ),
}


# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------

def load_asr_model():
    """Load Indic Conformer."""

    from transformers import AutoModel

    model = AutoModel.from_pretrained(
        "ai4bharat/indic-conformer-600m-multilingual",
        trust_remote_code=True,
    )

    model.eval()

    return model


def _load_wav_as_mono_tensor(
    audio_path: str,
    target_sr: int = 16000,
) -> torch.Tensor:
    """
    Load WAV/FLAC using SoundFile.

    Returns:
        torch.FloatTensor with shape (1, samples)
    """

    try:

        data, sr = sf.read(
            audio_path,
            dtype="float32",
            always_2d=True,
        )

    except Exception as e:

        raise RuntimeError(
            f"Could not read audio file at {audio_path}. "
            f"Make sure it is a valid WAV/FLAC file. "
            f"Original error: {e}"
        )

    # Convert stereo/multichannel -> mono.
    mono = data.mean(axis=1)

    # Resample to 16 kHz if necessary.
    if sr != target_sr:

        g = math.gcd(sr, target_sr)

        mono = resample_poly(
            mono,
            target_sr // g,
            sr // g,
        ).astype(np.float32)

    wav = torch.from_numpy(
        mono.astype(np.float32)
    ).unsqueeze(0)

    return wav


def transcribe(
    model,
    audio_path: str,
    lang_code: str,
    decoding: str = "ctc",
) -> str:
    """Transcribe recorded speech."""

    wav = _load_wav_as_mono_tensor(
        audio_path,
        target_sr=16000,
    )

    with torch.no_grad():

        transcription = model(
            wav,
            lang_code,
            decoding,
        )

    return transcription


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

def load_tts_model():
    """
    Initialize TTS engine.
    Prioritizes fast lightweight gTTS for instant responsiveness,
    with fallback to AI4Bharat Parler-TTS if specifically installed.
    """
    # 1. Check for gTTS (fast, zero CPU load, crisp Indian language support)
    try:
        import gtts
        return {"engine": "gtts"}
    except ImportError:
        pass

    # 2. Check for Parler-TTS if available
    try:
        from parler_tts import (
            ParlerTTSForConditionalGeneration
        )
        from transformers import AutoTokenizer

        device = (
            "cuda:0"
            if torch.cuda.is_available()
            else "cpu"
        )

        model = (
            ParlerTTSForConditionalGeneration
            .from_pretrained(
                "ai4bharat/indic-parler-tts"
            )
            .to(device)
        )
        model.eval()

        tokenizer = AutoTokenizer.from_pretrained(
            "ai4bharat/indic-parler-tts"
        )
        description_tokenizer = AutoTokenizer.from_pretrained(
            model.config.text_encoder._name_or_path
        )

        return {
            "engine": "parler",
            "model": model,
            "tokenizer": tokenizer,
            "description_tokenizer": description_tokenizer,
            "device": device,
        }
    except Exception as e:
        return {"engine": "fallback", "error": str(e)}


def synthesize(
    tts_bundle,
    text: str,
    lang_code: str,
    out_path: str = "reply.mp3",
):
    """
    Generate spoken audio from text.
    Supports fast gTTS, Indic Parler-TTS, and graceful fallbacks.
    """
    if not text or not str(text).strip():
        return None

    import os
    text_clean = str(text).strip()

    # Normalize bundle format
    if not isinstance(tts_bundle, dict):
        if isinstance(tts_bundle, (list, tuple)) and len(tts_bundle) == 4:
            tts_bundle = {
                "engine": "parler",
                "model": tts_bundle[0],
                "tokenizer": tts_bundle[1],
                "description_tokenizer": tts_bundle[2],
                "device": tts_bundle[3],
            }
        else:
            tts_bundle = {"engine": "gtts"}

    engine = tts_bundle.get("engine", "gtts")

    # Fast gTTS path
    if engine == "gtts":
        try:
            import gtts
            supported_lang = lang_code if lang_code in ["hi", "mr", "ta", "te", "bn", "gu", "en"] else "hi"
            tts = gtts.gTTS(text=text_clean, lang=supported_lang, slow=False)
            
            os.makedirs(os.path.dirname(os.path.abspath(out_path)) if os.path.dirname(out_path) else ".", exist_ok=True)
            tts.save(out_path)
            return out_path
        except Exception as e:
            print("gTTS error:", e)
            return None

    # Neural Parler-TTS path
    elif engine == "parler":
        try:
            model = tts_bundle["model"]
            tokenizer = tts_bundle["tokenizer"]
            description_tokenizer = tts_bundle["description_tokenizer"]
            device = tts_bundle["device"]

            description = TTS_VOICE_DESCRIPTIONS.get(
                lang_code,
                TTS_VOICE_DESCRIPTIONS["hi"],
            )

            description_inputs = description_tokenizer(
                description,
                return_tensors="pt",
            ).to(device)

            prompt_inputs = tokenizer(
                text_clean,
                return_tensors="pt",
            ).to(device)

            with torch.no_grad():
                generation = model.generate(
                    input_ids=description_inputs.input_ids,
                    attention_mask=description_inputs.attention_mask,
                    prompt_input_ids=prompt_inputs.input_ids,
                    prompt_attention_mask=prompt_inputs.attention_mask,
                )

            audio = (
                generation
                .cpu()
                .numpy()
                .squeeze()
            )

            os.makedirs(os.path.dirname(os.path.abspath(out_path)) if os.path.dirname(out_path) else ".", exist_ok=True)
            sf.write(
                out_path,
                audio,
                model.config.sampling_rate,
            )
            return out_path
        except Exception as e:
            print("Parler TTS error:", e)
            return None

    return None
 