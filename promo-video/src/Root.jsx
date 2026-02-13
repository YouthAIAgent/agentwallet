import { Composition, staticFile } from 'remotion';
import { MainPromo } from './compositions/MainPromo';
import { FeatureHighlight } from './compositions/FeatureHighlight';
import { ArchExplainer } from './compositions/ArchExplainer';
import { TwitterCard } from './compositions/TwitterCard';
import { StatsNumbers } from './compositions/StatsNumbers';
import { FullExplainer } from './compositions/FullExplainer';
import { ProductDemo } from './compositions/ProductDemo';
import { HackathonDemo } from './compositions/HackathonDemo';
import { FuturisticPromo } from './compositions/FuturisticPromo';
import { TokenDetails } from './compositions/TokenDetails';

// Keep the original composition for backwards compat
import { AgentWalletPromo } from './AgentWalletPromo';

const FPS = 60;

export const RemotionRoot = () => {
  return (
    <>
      {/* ═══════════════════════════════════════════════════
          TOKEN DETAILS (55s, 1920x1080, 30fps)
         ═══════════════════════════════════════════════════ */}
      <Composition
        id="TokenDetails"
        component={TokenDetails}
        durationInFrames={30 * 66}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          voiceoverSrc: staticFile('token-details-vo.mp3'),
        }}
      />

      {/* ═══════════════════════════════════════════════════
          2030 FUTURISTIC PROMO (30s, 1920x1080, 30fps)
         ═══════════════════════════════════════════════════ */}
      <Composition
        id="FuturisticPromo"
        component={FuturisticPromo}
        durationInFrames={30 * 28}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* ═══════════════════════════════════════════════════
          HACKATHON DEMO (60s, 1920x1080, 30fps)
         ═══════════════════════════════════════════════════ */}
      <Composition
        id="HackathonDemo"
        component={HackathonDemo}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* ═══════════════════════════════════════════════════
          PRODUCT DEMO (60s, 1920x1080, 30fps)
         ═══════════════════════════════════════════════════ */}
      <Composition
        id="ProductDemo"
        component={ProductDemo}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* ═══════════════════════════════════════════════════
          FULL EXPLAINER (4 min, 1920x1080, 60fps)
         ═══════════════════════════════════════════════════ */}
      <Composition
        id="FullExplainer"
        component={FullExplainer}
        durationInFrames={Math.ceil(242 * FPS)}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          voiceoverSrc: staticFile('full-explainer-vo.mp3'),
        }}
      />

      {/* ═══════════════════════════════════════════════════
          LANDSCAPE (1920x1080) — 60fps Professional
         ═══════════════════════════════════════════════════ */}

      {/* Template A: Architecture Explainer (30-60s) */}
      <Composition
        id="ArchExplainer"
        component={ArchExplainer}
        durationInFrames={FPS * 40}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      {/* Template B: Feature Showcase (15-30s) */}
      <Composition
        id="FeatureHighlight"
        component={FeatureHighlight}
        durationInFrames={FPS * 15}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      {/* Template C: Stats/Numbers (10-15s) */}
      <Composition
        id="StatsNumbers"
        component={StatsNumbers}
        durationInFrames={FPS * 12}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      {/* Main Promo (30s) */}
      <Composition
        id="MainPromo"
        component={MainPromo}
        durationInFrames={FPS * 30}
        fps={FPS}
        width={1920}
        height={1080}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      {/* Twitter Card (5s) */}
      <Composition
        id="TwitterCard"
        component={TwitterCard}
        durationInFrames={FPS * 5}
        fps={FPS}
        width={1200}
        height={675}
      />

      {/* ═══════════════════════════════════════════════════
          VERTICAL / SHORTS (1080x1920) — 60fps
         ═══════════════════════════════════════════════════ */}

      <Composition
        id="ArchExplainer-Vertical"
        component={ArchExplainer}
        durationInFrames={FPS * 40}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      <Composition
        id="FeatureHighlight-Vertical"
        component={FeatureHighlight}
        durationInFrames={FPS * 15}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      <Composition
        id="StatsNumbers-Vertical"
        component={StatsNumbers}
        durationInFrames={FPS * 12}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      <Composition
        id="MainPromo-Vertical"
        component={MainPromo}
        durationInFrames={FPS * 30}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={{
          voiceoverSrc: '',
        }}
      />

      {/* ═══════════════════════════════════════════════════
          LEGACY (backwards compatible)
         ═══════════════════════════════════════════════════ */}
      <Composition
        id="AgentWalletPromo"
        component={AgentWalletPromo}
        durationInFrames={450}
        fps={30}
        width={1280}
        height={720}
      />
    </>
  );
};
