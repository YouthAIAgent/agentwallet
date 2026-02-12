"""
AgentWallet Voice Engine v3.0
==============================
ElevenLabs (premium) + Edge TTS (free unlimited fallback)
Multi-key rotation for ElevenLabs.

Usage:
    from voice import generate_voiceover
    generate_voiceover("Your AI agent needs a wallet.", "output.mp3", voice="eric")
    
    # Edge TTS (free, unlimited):
    generate_voiceover("Hello world", "out.mp3", voice="edge-andrew")
    
    # CLI:
    python voice.py --text "Hello world" --output hello.mp3 --voice eric
    python voice.py --text "Hello world" --output hello.mp3 --voice edge-andrew
    python voice.py --list-voices
"""

import json
import os
import sys
import argparse
import asyncio
import requests
from pathlib import Path

try:
    from mutagen.mp3 import MP3
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

try:
    import edge_tts
    HAS_EDGE = True
except ImportError:
    HAS_EDGE = False


# ─── ElevenLabs Voice Configuration ───
ELEVENLABS_VOICES = {
    "eric": {
        "id": "cjVigY5qzO86Huf0OWal",
        "description": "Smooth, professional narrator. Perfect for explainer videos."
    },
    "george": {
        "id": "JBFqnCBsd6RMkjVDRZzb",
        "description": "British accent, premium feel. Great for product launches."
    },
    "liam": {
        "id": "TX3LPaxmHKxFdv7VOQHJ",
        "description": "Energetic and punchy. Perfect for shorts and social clips."
    },
    "brian": {
        "id": "nPczCjzI2devNBz1zQrb",
        "description": "Deep and authoritative. Best for technical content."
    },
    "drew": {
        "id": "29vD33N1CtxCmqQRPOHJ",
        "description": "Warm and conversational. Good for tutorials."
    },
}

# ─── Edge TTS Voice Configuration (FREE, UNLIMITED) ───
EDGE_VOICES = {
    "edge-andrew": {
        "id": "en-US-AndrewNeural",
        "description": "US Male, confident and clear. Best free voice for tech."
    },
    "edge-brian": {
        "id": "en-US-BrianNeural",
        "description": "US Male, warm and natural."
    },
    "edge-guy": {
        "id": "en-US-GuyNeural",
        "description": "US Male, casual and friendly."
    },
    "edge-roger": {
        "id": "en-US-RogerNeural",
        "description": "US Male, deep and authoritative."
    },
    "edge-chris": {
        "id": "en-US-ChristopherNeural",
        "description": "US Male, professional newsreader."
    },
    "edge-eric": {
        "id": "en-US-EricNeural",
        "description": "US Male, smooth and steady."
    },
    "edge-ryan": {
        "id": "en-GB-RyanNeural",
        "description": "British Male, premium feel."
    },
    "edge-thomas": {
        "id": "en-GB-ThomasNeural",
        "description": "British Male, warm storyteller."
    },
    "edge-emma": {
        "id": "en-US-EmmaNeural",
        "description": "US Female, clear and engaging."
    },
    "edge-ava": {
        "id": "en-US-AvaNeural",
        "description": "US Female, confident and polished."
    },
    "edge-prabhat": {
        "id": "en-IN-PrabhatNeural",
        "description": "Indian Male, great for Hindi-English content."
    },
}

MODEL_ID = "eleven_multilingual_v2"
API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
SECRETS_PATH = Path.home() / ".openclaw" / "secrets" / "elevenlabs.json"


def _load_api_keys() -> list:
    """Load all ElevenLabs API keys from secrets file."""
    keys = []
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH, "r") as f:
            data = json.load(f)
            # Support: api_key, api_key_2, api_key_3, ... or keys: [...]
            if "keys" in data:
                keys = data["keys"]
            else:
                for k, v in data.items():
                    if k.startswith("api_key") and v:
                        keys.append(v)
    
    # Also check env var
    env_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if env_key and env_key not in keys:
        keys.append(env_key)
    
    return keys


def get_audio_duration(filepath: str) -> float:
    """Get duration of an MP3 file in seconds."""
    if HAS_MUTAGEN:
        try:
            audio = MP3(filepath)
            return audio.info.length
        except Exception:
            pass
    # Fallback: estimate from file size (128kbps)
    file_size = os.path.getsize(filepath)
    return file_size / (128 * 1024 / 8)


def _generate_edge_tts(script_text: str, output_path: str, voice_id: str) -> dict:
    """Generate voiceover using Edge TTS (free, unlimited)."""
    if not HAS_EDGE:
        raise RuntimeError("edge-tts not installed. Run: pip install edge-tts")
    
    async def _run():
        communicate = edge_tts.Communicate(script_text, voice_id)
        await communicate.save(output_path)
    
    asyncio.run(_run())
    
    duration = get_audio_duration(output_path)
    return {
        "output_path": os.path.abspath(output_path),
        "duration_seconds": round(duration, 2),
        "engine": "edge-tts",
        "voice_id": voice_id,
        "characters": len(script_text),
        "file_size_kb": round(os.path.getsize(output_path) / 1024, 1),
        "cost": "$0.00 (free)",
    }


def _generate_elevenlabs(script_text: str, output_path: str, voice_id: str,
                          stability: float, similarity_boost: float, style: float) -> dict:
    """Generate voiceover using ElevenLabs with multi-key rotation."""
    keys = _load_api_keys()
    if not keys:
        raise RuntimeError(
            f"No ElevenLabs API keys found at {SECRETS_PATH} or ELEVENLABS_API_KEY env."
        )
    
    url = f"{API_URL}/{voice_id}"
    payload = {
        "text": script_text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": True,
        },
    }
    
    last_error = None
    for i, key in enumerate(keys):
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": key,
        }
        
        try:
            print(f"[VOICE] Trying ElevenLabs key {i+1}/{len(keys)}...")
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                duration = get_audio_duration(output_path)
                return {
                    "output_path": os.path.abspath(output_path),
                    "duration_seconds": round(duration, 2),
                    "engine": "elevenlabs",
                    "key_index": i + 1,
                    "characters": len(script_text),
                    "file_size_kb": round(os.path.getsize(output_path) / 1024, 1),
                }
            
            elif response.status_code == 401:
                print(f"[VOICE] Key {i+1} unauthorized, trying next...")
                last_error = f"Key {i+1}: 401 Unauthorized"
            elif response.status_code == 429:
                print(f"[VOICE] Key {i+1} quota exceeded, trying next...")
                last_error = f"Key {i+1}: 429 Quota exceeded"
            else:
                print(f"[VOICE] Key {i+1} error {response.status_code}, trying next...")
                last_error = f"Key {i+1}: {response.status_code} {response.text[:100]}"
                
        except Exception as e:
            print(f"[VOICE] Key {i+1} failed: {e}")
            last_error = str(e)
    
    raise RuntimeError(f"All {len(keys)} ElevenLabs keys failed. Last error: {last_error}")


def generate_voiceover(
    script_text: str,
    output_path: str,
    voice: str = "eric",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    fallback_to_edge: bool = True,
) -> dict:
    """
    Generate voiceover audio. Tries ElevenLabs first, falls back to Edge TTS.
    
    Args:
        script_text: Text to convert to speech
        output_path: Where to save the MP3 file
        voice: Voice name (ElevenLabs: eric/george/liam/brian/drew, Edge: edge-andrew/edge-brian/etc)
        stability: ElevenLabs voice stability (0-1)
        similarity_boost: ElevenLabs voice clarity (0-1)
        style: ElevenLabs style exaggeration (0-1)
        fallback_to_edge: If ElevenLabs fails, auto-fallback to Edge TTS
    
    Returns:
        dict with: output_path, duration_seconds, engine, characters, file_size_kb
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    voice_lower = voice.lower()
    
    # Edge TTS voice requested directly
    if voice_lower.startswith("edge-"):
        if voice_lower not in EDGE_VOICES:
            available = ", ".join(EDGE_VOICES.keys())
            raise ValueError(f"Unknown Edge voice '{voice}'. Available: {available}")
        
        voice_config = EDGE_VOICES[voice_lower]
        print(f"[VOICE] Engine: Edge TTS (FREE)")
        print(f"[VOICE] Voice: {voice} ({voice_config['description']})")
        print(f"[VOICE] Characters: {len(script_text)}")
        
        result = _generate_edge_tts(script_text, output_path, voice_config["id"])
        print(f"[VOICE] [OK] Saved to {output_path}")
        print(f"[VOICE] [OK] Duration: {result['duration_seconds']}s | Size: {result['file_size_kb']}KB | Cost: FREE")
        return result
    
    # ElevenLabs voice requested
    if voice_lower not in ELEVENLABS_VOICES:
        all_voices = list(ELEVENLABS_VOICES.keys()) + list(EDGE_VOICES.keys())
        available = ", ".join(all_voices)
        raise ValueError(f"Unknown voice '{voice}'. Available: {available}")
    
    voice_config = ELEVENLABS_VOICES[voice_lower]
    print(f"[VOICE] Engine: ElevenLabs (Premium)")
    print(f"[VOICE] Voice: {voice} ({voice_config['description']})")
    print(f"[VOICE] Characters: {len(script_text)}")
    
    try:
        result = _generate_elevenlabs(
            script_text, output_path, voice_config["id"],
            stability, similarity_boost, style
        )
        print(f"[VOICE] [OK] Saved to {output_path}")
        print(f"[VOICE] [OK] Duration: {result['duration_seconds']}s | Size: {result['file_size_kb']}KB | Key: {result['key_index']}")
        return result
        
    except RuntimeError as e:
        if fallback_to_edge:
            print(f"[VOICE] ElevenLabs failed: {e}")
            print(f"[VOICE] Falling back to Edge TTS (free)...")
            
            # Map ElevenLabs voice to closest Edge equivalent
            edge_fallback = {
                "eric": "edge-eric",
                "george": "edge-ryan",
                "liam": "edge-andrew",
                "brian": "edge-roger",
                "drew": "edge-brian",
            }
            fallback_voice = edge_fallback.get(voice_lower, "edge-andrew")
            edge_config = EDGE_VOICES[fallback_voice]
            
            print(f"[VOICE] Fallback voice: {fallback_voice} ({edge_config['description']})")
            result = _generate_edge_tts(script_text, output_path, edge_config["id"])
            print(f"[VOICE] [OK] Fallback saved to {output_path}")
            print(f"[VOICE] [OK] Duration: {result['duration_seconds']}s | Cost: FREE")
            return result
        else:
            raise


def list_voices():
    """Print all available voices."""
    print("\n  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║              AgentWallet Voice Engine v3.0                   ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    
    print("\n  🔮 ElevenLabs (Premium — auto-rotates API keys):")
    print("  " + "─" * 60)
    for name, config in ELEVENLABS_VOICES.items():
        print(f"    {name:>8}  │  {config['description']}")
    
    print(f"\n  🆓 Edge TTS (FREE — unlimited, no API key needed):")
    print("  " + "─" * 60)
    for name, config in EDGE_VOICES.items():
        print(f"    {name:>14}  │  {config['description']}")
    
    keys = _load_api_keys()
    print(f"\n  🔑 ElevenLabs API keys loaded: {len(keys)}")
    print(f"  📁 Secrets path: {SECRETS_PATH}")
    print()


# ─── CLI ───
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate voiceover audio (ElevenLabs + Edge TTS fallback)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # ElevenLabs (premium, auto key rotation)
  python voice.py --text "AgentWallet is the future." --output vo.mp3 --voice eric
  
  # Edge TTS (free, unlimited)  
  python voice.py --text "Hello world" --output hello.mp3 --voice edge-andrew
  
  # Auto-fallback: tries ElevenLabs, falls back to Edge TTS if quota exceeded
  python voice.py --text "Demo text" --output demo.mp3 --voice liam
  
  # Force Edge only (no ElevenLabs attempt)
  python voice.py --text "Free voice" --output free.mp3 --voice edge-roger
  
  # List all voices
  python voice.py --list-voices
        """,
    )
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument("--file", type=str, help="Text file to read script from")
    parser.add_argument("--output", "-o", type=str, default="voiceover.mp3", help="Output MP3 path")
    parser.add_argument("--voice", "-v", type=str, default="eric", help="Voice name")
    parser.add_argument("--stability", type=float, default=0.5, help="ElevenLabs stability (0-1)")
    parser.add_argument("--similarity", type=float, default=0.75, help="ElevenLabs similarity (0-1)")
    parser.add_argument("--style", type=float, default=0.0, help="ElevenLabs style (0-1)")
    parser.add_argument("--no-fallback", action="store_true", help="Disable Edge TTS fallback")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    
    args = parser.parse_args()
    
    if args.list_voices:
        list_voices()
        sys.exit(0)
    
    script_text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
    
    if not script_text:
        parser.error("Provide --text or --file with the script content")
    
    try:
        result = generate_voiceover(
            script_text=script_text,
            output_path=args.output,
            voice=args.voice,
            stability=args.stability,
            similarity_boost=args.similarity,
            style=args.style,
            fallback_to_edge=not args.no_fallback,
        )
        engine = result.get("engine", "unknown")
        cost = result.get("cost", "paid") if engine == "edge-tts" else "credits used"
        print(f"\n  ✅ Done! {result['duration_seconds']}s voiceover → {result['output_path']} [{engine}]")
    except Exception as e:
        print(f"\n  ❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)
