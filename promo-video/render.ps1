# AgentWallet Promo Video Render Script
# Usage: .\render.ps1
# Requires: Node.js, Remotion, ffmpeg (bundled with Remotion)

Set-Location "C:\Users\black\Desktop\agentwallet\promo-video"

Write-Host "🎬 AgentWallet Video Pipeline — Rendering all compositions..." -ForegroundColor Cyan
Write-Host ""

# Create output directory
New-Item -ItemType Directory -Path "out" -Force | Out-Null

# MainPromo — 30s flagship video
Write-Host "🎥 [1/4] Rendering MainPromo (30s, 1280x720)..." -ForegroundColor Yellow
npx remotion render MainPromo out/main-promo.mp4 --codec h264
Write-Host "✅ MainPromo done!" -ForegroundColor Green
Write-Host ""

# FeatureHighlight — 15s feature showcase
Write-Host "🎥 [2/4] Rendering FeatureHighlight (15s, 1280x720)..." -ForegroundColor Yellow
npx remotion render FeatureHighlight out/feature-highlight.mp4 --codec h264
Write-Host "✅ FeatureHighlight done!" -ForegroundColor Green
Write-Host ""

# ArchExplainer — 20s architecture walkthrough
Write-Host "🎥 [3/4] Rendering ArchExplainer (20s, 1280x720)..." -ForegroundColor Yellow
npx remotion render ArchExplainer out/arch-explainer.mp4 --codec h264
Write-Host "✅ ArchExplainer done!" -ForegroundColor Green
Write-Host ""

# TwitterCard — 5s animated card
Write-Host "🎥 [4/4] Rendering TwitterCard (5s, 1200x675)..." -ForegroundColor Yellow
npx remotion render TwitterCard out/twitter-card.mp4 --codec h264
Write-Host "✅ TwitterCard done!" -ForegroundColor Green
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎬 All renders complete! Files in out/" -ForegroundColor Cyan
Write-Host "  out/main-promo.mp4" -ForegroundColor White
Write-Host "  out/feature-highlight.mp4" -ForegroundColor White
Write-Host "  out/arch-explainer.mp4" -ForegroundColor White
Write-Host "  out/twitter-card.mp4" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
