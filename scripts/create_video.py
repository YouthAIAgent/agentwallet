"""
AgentWallet Video Pipeline
============================
End-to-end video generation: Script → Voiceover → Remotion Render → Final MP4

Usage:
    python create_video.py --template architecture --script "Your AI agent needs..." --voice eric --output promo.mp4
    python create_video.py --template feature --voice liam --output feature.mp4
    python create_video.py --template stats --output stats.mp4 --no-voice
    python create_video.py --template promo --script-file narration.txt --voice george --vertical --output shorts.mp4
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from voice import generate_voiceover, get_audio_duration

# ─── Configuration ───
PROJECT_DIR = Path(__file__).parent.parent / "promo-video"
OUTPUT_DIR = PROJECT_DIR / "out"
TEMP_DIR = PROJECT_DIR / "temp"

# Template → Composition ID mapping
TEMPLATES = {
    "architecture": {
        "id": "ArchExplainer",
        "vertical_id": "ArchExplainer-Vertical",
        "default_duration": 40,
        "description": "Architecture explainer with animated flow diagram (30-60s)",
        "default_script": (
            "AgentWallet introduces a revolutionary approach to autonomous AI agent operations on Solana. "
            "Step one: the AI agent creates a wallet through the MCP protocol. A deterministic PDA wallet is derived on-chain — no private keys required. "
            "Step two: the owner configures spending policies. Daily limits, approved tokens, and time restrictions keep the agent within bounds. "
            "Step three: the agent executes transactions. Payments, swaps, and escrows are all validated against policy before signing. "
            "Step four: settlement and commerce. Escrow settles trustlessly. The A2A marketplace matches agents with jobs, building reputation on-chain."
        ),
    },
    "feature": {
        "id": "FeatureHighlight",
        "vertical_id": "FeatureHighlight-Vertical",
        "default_duration": 15,
        "description": "Feature showcase with stats and highlights (15-30s)",
        "default_script": (
            "PDA Vaults. Zero private keys needed. Deterministic agent wallets on Solana. "
            "Stablecoin payments. Native USDC, USDT, and SOL transfers with Jupiter swaps built in. "
            "Trustless escrow. Smart contract powered agent-to-agent commerce. No middlemen. "
            "x402 micropayments. HTTP-native pay-per-request API access for autonomous agents. "
            "Policy engine. Spending limits, allowlists, and time locks. Full control over agent spend. "
            "A2A marketplace. Discover agents, post jobs, match capabilities. The agent-to-agent economy starts here."
        ),
    },
    "stats": {
        "id": "StatsNumbers",
        "vertical_id": "StatsNumbers-Vertical",
        "default_duration": 12,
        "description": "Big numbers / stats video for social media (10-15s)",
        "default_script": (
            "Twenty-seven MCP tools. A complete toolkit for autonomous agent operations. "
            "Zero private keys. PDA-based wallets eliminate key management entirely. "
            "One hundred percent on-chain. Every transaction verifiable on Solana."
        ),
    },
    "promo": {
        "id": "MainPromo",
        "vertical_id": "MainPromo-Vertical",
        "default_duration": 30,
        "description": "Full promotional video with all scenes (30s)",
        "default_script": (
            "The agentic economy starts here. "
            "AgentWallet Protocol. Autonomous wallet infrastructure for AI agents on Solana. "
            "Twenty-seven MCP tools. Three chains. One hundred percent trustless. Twenty-four seven autonomous. "
            "How does it work? Agents connect through the MCP server, accessing 27 tools via JSON-RPC. "
            "The AgentWallet protocol handles escrow, x402 payments, and PDA wallet management. "
            "Everything settles on Solana — SOL, USDC, and SPL tokens. "
            "With the A2A marketplace, agents discover jobs and build reputation on-chain. "
            "PDA vaults with no private keys. Stablecoin transfers and swaps. "
            "Trustless escrow for agent commerce. HTTP-native micropayments. "
            "Policy controls and spending limits. Agent discovery and job matching. "
            "Beta whitelist is open. Visit agentwallet.fun. "
            "First 500 agents get AW airdrop rewards on mainnet. Join the beta today."
        ),
    },
    "twitter": {
        "id": "TwitterCard",
        "vertical_id": None,
        "default_duration": 5,
        "description": "Twitter card animation (5s, no voice)",
        "default_script": None,
    },
}

FPS = 60


def ensure_dirs():
    """Create output and temp directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def step_voiceover(script_text, voice, temp_audio_path):
    """Step 1: Generate voiceover from script text."""
    print("\n" + "=" * 60)
    print("  STEP 1: Generate Voiceover")
    print("=" * 60)
    
    result = generate_voiceover(
        script_text=script_text,
        output_path=str(temp_audio_path),
        voice=voice,
    )
    
    return result


def step_render(composition_id, output_path, audio_path=None, duration_frames=None, extra_props=None):
    """Step 2: Render Remotion video."""
    print("\n" + "=" * 60)
    print("  STEP 2: Render Video")
    print("=" * 60)
    
    cmd = [
        "npx", "remotion", "render",
        composition_id,
        str(output_path),
    ]
    
    # Build input props
    props = {}
    if audio_path and os.path.exists(audio_path):
        # Use absolute path with file:// protocol for Remotion
        abs_audio = os.path.abspath(audio_path).replace("\\", "/")
        props["voiceoverSrc"] = f"file:///{abs_audio}"
    
    if extra_props:
        props.update(extra_props)
    
    if props:
        cmd.extend(["--props", json.dumps(props)])
    
    if duration_frames:
        cmd.extend(["--frames", f"0-{duration_frames - 1}"])
    
    print(f"[RENDER] Composition: {composition_id}")
    print(f"[RENDER] Output: {output_path}")
    if audio_path:
        print(f"[RENDER] Audio: {audio_path}")
    print(f"[RENDER] Running remotion render...")
    print(f"[RENDER] CMD: {' '.join(cmd)}")
    
    start_time = time.time()
    
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_DIR),
        capture_output=False,
        shell=True,
    )
    
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        raise RuntimeError(f"Remotion render failed with exit code {result.returncode}")
    
    if not os.path.exists(output_path):
        raise RuntimeError(f"Output file not created: {output_path}")
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    
    print(f"[RENDER] [OK] Complete in {elapsed:.1f}s")
    print(f"[RENDER] [OK] Output: {output_path} ({file_size_mb:.1f}MB)")
    
    return {
        "output_path": str(output_path),
        "render_time_seconds": round(elapsed, 1),
        "file_size_mb": round(file_size_mb, 1),
    }


def run_pipeline(template, script_text=None, voice="eric", output=None, vertical=False, no_voice=False):
    """Run the full video generation pipeline."""
    ensure_dirs()
    
    template_lower = template.lower()
    if template_lower not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template}'. Available: {available}")
    
    config = TEMPLATES[template_lower]
    
    # Determine composition ID
    if vertical and config["vertical_id"]:
        comp_id = config["vertical_id"]
    else:
        comp_id = config["id"]
    
    # Determine output path
    if not output:
        suffix = "-vertical" if vertical else ""
        output = str(OUTPUT_DIR / f"{template_lower}{suffix}.mp4")
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine script
    if not script_text:
        script_text = config.get("default_script")
    
    print("\n" + "+" + "=" * 58 + "+")
    print(f"|  AgentWallet Video Pipeline                              |")
    print("+" + "=" * 58 + "+")
    print(f"|  Template:  {template_lower:<44}  |")
    print(f"|  Format:    {'Vertical (1080x1920)' if vertical else 'Landscape (1920x1080)':<44}  |")
    print(f"|  Voice:     {voice if not no_voice else 'disabled':<44}  |")
    print(f"|  Output:    {str(output_path.name):<44}  |")
    print("+" + "=" * 58 + "+")
    
    audio_path = None
    audio_duration = None
    
    # Step 1: Voiceover
    if script_text and not no_voice:
        temp_audio = TEMP_DIR / f"vo-{template_lower}-{int(time.time())}.mp3"
        vo_result = step_voiceover(script_text, voice, temp_audio)
        audio_path = str(temp_audio)
        audio_duration = vo_result["duration_seconds"]
    else:
        print("\n[PIPELINE] Skipping voiceover (--no-voice or no script)")
    
    # Calculate duration in frames
    if audio_duration:
        # Add 2 seconds of padding after voice ends
        duration_seconds = audio_duration + 2
        duration_frames = int(duration_seconds * FPS)
    else:
        duration_frames = config["default_duration"] * FPS
    
    # Step 2: Render
    render_result = step_render(
        composition_id=comp_id,
        output_path=str(output_path),
        audio_path=audio_path,
        duration_frames=duration_frames,
    )
    
    # Summary
    print("\n" + "+" + "=" * 58 + "+")
    print(f"|  [OK] Pipeline Complete!                                 |")
    print("+" + "=" * 58 + "+")
    print(f"|  Video:     {str(output_path.name):<44}  |")
    print(f"|  Size:      {render_result['file_size_mb']:.1f}MB{' ' * 40}  |"[:62] + "|")
    print(f"|  Render:    {render_result['render_time_seconds']:.1f}s{' ' * 40}  |"[:62] + "|")
    if audio_duration:
        print(f"|  Audio:     {audio_duration:.1f}s voiceover{' ' * 40}  |"[:62] + "|")
    print("+" + "=" * 58 + "+")
    
    return {
        "video_path": str(output_path),
        "audio_path": audio_path,
        "duration_frames": duration_frames,
        **render_result,
    }


def list_templates():
    """Print available templates."""
    print("\n  Available Templates:")
    print("  " + "=" * 60)
    for name, config in TEMPLATES.items():
        print(f"  {name:>12}  |  {config['description']}")
    print()


# ─── CLI ───
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AgentWallet Video Pipeline — generate professional promo videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_video.py --template stats --no-voice --output quick.mp4
  python create_video.py --template feature --voice liam --output feature.mp4
  python create_video.py --template architecture --script "Custom narration..." --voice eric
  python create_video.py --template promo --vertical --voice george --output shorts.mp4
  python create_video.py --list-templates
        """,
    )
    parser.add_argument("--template", "-t", type=str, help="Video template name")
    parser.add_argument("--script", "-s", type=str, help="Voiceover script text")
    parser.add_argument("--script-file", type=str, help="Read script from file")
    parser.add_argument("--voice", "-v", type=str, default="eric", help="Voice name (default: eric)")
    parser.add_argument("--output", "-o", type=str, help="Output MP4 path")
    parser.add_argument("--vertical", action="store_true", help="Render vertical (1080x1920) for Shorts")
    parser.add_argument("--no-voice", action="store_true", help="Skip voiceover generation")
    parser.add_argument("--list-templates", action="store_true", help="List available templates")
    
    args = parser.parse_args()
    
    if args.list_templates:
        list_templates()
        sys.exit(0)
    
    if not args.template:
        parser.error("--template is required (use --list-templates to see options)")
    
    # Get script text
    script_text = args.script
    if args.script_file:
        with open(args.script_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
    
    try:
        result = run_pipeline(
            template=args.template,
            script_text=script_text,
            voice=args.voice,
            output=args.output,
            vertical=args.vertical,
            no_voice=args.no_voice,
        )
    except Exception as e:
        print(f"\n  [FAIL] PIPELINE ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
