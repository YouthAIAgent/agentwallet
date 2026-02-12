import React, { useMemo } from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from 'remotion';
import { fontFamily } from '../fonts';
import { theme, hexToRgb, easing } from '../theme';
import { Background } from '../components/Background';
import { GlitchText } from '../components/GlitchText';
import { FadeSlide } from '../components/FadeSlide';
import { ParticleExplosion } from '../components/ParticleExplosion';

const FPS = 30;

// Scene boundaries (frames at 30fps)
const S1_START = 0;
const S1_END = 240;    // 0-8s
const S2_START = 240;
const S2_END = 600;    // 8-20s
const S3_START = 600;
const S3_END = 1050;   // 20-35s
const S4_START = 1050;
const S4_END = 1500;   // 35-50s
const S5_START = 1500;
const S5_END = 1800;   // 50-60s

/* ═════════════════════════════════════════════════════════════
   SCENE 1 — Terminal Boot
   ═════════════════════════════════════════════════════════════ */
const termLines = [
  { text: '$ pip install agentwallet-mcp', cmd: true, delay: 15 },
  { text: '✓ Installing agentwallet v0.4.2...', cmd: false, delay: 55 },
  { text: '✓ 27 MCP tools loaded', cmd: false, delay: 80 },
  { text: '✓ Solana mainnet connected', cmd: false, delay: 105 },
  { text: '', cmd: false, delay: 125, blank: true },
  { text: '$ agentwallet init --agent claude-opus', cmd: true, delay: 135 },
  { text: '✓ PDA vault created: 7xKp...3mNq', cmd: false, delay: 175 },
  { text: '✓ Agent wallet LIVE', cmd: false, delay: 200, live: true },
];

const TermLine = ({ line, frame }) => {
  const el = frame - line.delay;
  if (el < 0 || line.blank) return line.blank ? <div style={{ height: 8 }} /> : null;

  const spd = line.cmd ? 1.2 : 2.5;
  const chars = Math.min(Math.floor(el * spd), line.text.length);
  const disp = line.text.slice(0, chars);
  const typing = chars < line.text.length;
  const cursorOn = typing && el % 10 < 6;
  const color = line.cmd ? '#E2E8F0' : '#14F195';
  const glow = line.live ? 0.8 : 0.3;
  const op = interpolate(el, [0, 3], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <div style={{
      fontFamily: fontFamily.mono, fontSize: 22, fontWeight: line.cmd ? 500 : 400,
      color, textShadow: `0 0 ${10*glow}px ${color}80, 0 0 ${20*glow}px ${color}40`,
      marginBottom: 6, opacity: op, whiteSpace: 'pre', letterSpacing: 0.5,
    }}>
      {disp}{cursorOn && <span style={{ color: '#9945FF', opacity: 0.9 }}>█</span>}
    </div>
  );
};

const Scene1 = () => {
  const frame = useCurrentFrame();
  const fadeOut = interpolate(frame, [S1_END-20, S1_END], [1, 0], { extrapolateLeft:'clamp', extrapolateRight:'clamp' });
  const boot = frame < 8
    ? interpolate(frame, [0,3,5,8], [0,1,0.6,1], { extrapolateLeft:'clamp', extrapolateRight:'clamp' })
    : 1;

  return (
    <AbsoluteFill style={{ justifyContent:'center', alignItems:'center', opacity: fadeOut * boot }}>
      <div style={{
        width: 900, background: 'rgba(0,0,0,0.85)', borderRadius: 12,
        border: '1px solid rgba(20,241,149,0.15)', padding: '24px 32px',
        boxShadow: '0 0 60px rgba(20,241,149,0.08), inset 0 0 40px rgba(0,0,0,0.5)',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Header bar */}
        <div style={{ display:'flex', gap:8, marginBottom:20, paddingBottom:12, borderBottom:'1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ width:12,height:12,borderRadius:'50%',background:'#FF5F56' }} />
          <div style={{ width:12,height:12,borderRadius:'50%',background:'#FFBD2E' }} />
          <div style={{ width:12,height:12,borderRadius:'50%',background:'#27C93F' }} />
          <span style={{ marginLeft:12, fontFamily:fontFamily.mono, fontSize:12, color:'rgba(255,255,255,0.3)', letterSpacing:1 }}>
            agentwallet — bash
          </span>
        </div>
        {termLines.map((l,i) => <TermLine key={i} line={l} frame={frame} />)}
        {/* CRT scanlines */}
        <div style={{
          position:'absolute', inset:0, pointerEvents:'none',
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)',
        }} />
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 2 — Dashboard View
   ═════════════════════════════════════════════════════════════ */
const txList = [
  { type:'Transfer', amt:'-0.05 SOL', to:'3Kf2...9xPq', time:'2s ago' },
  { type:'Swap', amt:'-2.1 SOL', to:'Jupiter DEX', time:'14s ago' },
  { type:'Stake', amt:'-5.0 SOL', to:'Marinade', time:'1m ago' },
  { type:'Transfer', amt:'+0.85 SOL', to:'8mNp...2kRt', time:'3m ago' },
  { type:'NFT Mint', amt:'-0.02 SOL', to:'Metaplex', time:'7m ago' },
];

const Glass = ({ children, style={}, glow, glowColor=theme.colors.purple }) => {
  const rgb = hexToRgb(glowColor);
  return (
    <div style={{
      background:'rgba(15,15,40,0.55)', border:'1px solid rgba(255,255,255,0.08)',
      borderRadius:16, padding:'20px 24px', position:'relative', overflow:'hidden',
      ...(glow ? { boxShadow:`0 0 30px rgba(${rgb},0.1), inset 0 0 30px rgba(${rgb},0.03)` } : {}),
      ...style,
    }}>
      <div style={{
        position:'absolute', top:0, left:'10%', right:'10%', height:1,
        background:'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)', pointerEvents:'none',
      }} />
      {children}
    </div>
  );
};

const Scene2 = () => {
  const frame = useCurrentFrame();
  const lf = frame - S2_START;
  const fadeIn = interpolate(lf, [0,15], [0,1], { extrapolateLeft:'clamp', extrapolateRight:'clamp' });
  const fadeOut = interpolate(lf, [S2_END-S2_START-20, S2_END-S2_START], [1,0], { extrapolateLeft:'clamp', extrapolateRight:'clamp' });
  const bp = easing.easeOutExpo(interpolate(lf, [20,60], [0,1], { extrapolateLeft:'clamp', extrapolateRight:'clamp' }));
  const balSOL = (12.847*bp).toFixed(3);
  const balUSD = (2441.93*bp).toFixed(2);
  const pulse = 0.6+Math.sin(lf*0.12)*0.4;

  return (
    <AbsoluteFill style={{ justifyContent:'center', alignItems:'center', opacity:fadeIn*fadeOut, padding:80 }}>
      <div style={{ width:'100%', maxWidth:1100 }}>
        {/* Header */}
        <FadeSlide startFrame={S2_START+5} duration={15} direction="up">
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:30 }}>
            <div style={{ display:'flex', alignItems:'center', gap:16 }}>
              <div style={{
                width:44,height:44,borderRadius:12,
                background:'linear-gradient(135deg,#9945FF,#14F195)',
                display:'flex',alignItems:'center',justifyContent:'center',
                fontSize:22,fontWeight:900,color:'#fff',fontFamily:fontFamily.heading,
              }}>A</div>
              <div>
                <div style={{ fontSize:20,fontWeight:700,color:theme.colors.white,fontFamily:fontFamily.heading }}>
                  claude-opus-agent-01
                </div>
                <div style={{ fontSize:13,color:theme.colors.dim,fontFamily:fontFamily.mono,letterSpacing:0.5 }}>
                  7xKp...3mNq
                </div>
              </div>
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:10 }}>
              <div style={{
                width:10,height:10,borderRadius:'50%',background:theme.colors.green,
                boxShadow:`0 0 ${12*pulse}px ${theme.colors.green}`, opacity:pulse,
              }} />
              <span style={{ fontSize:14,fontWeight:700,color:theme.colors.green,fontFamily:fontFamily.mono,letterSpacing:2 }}>
                LIVE
              </span>
            </div>
          </div>
        </FadeSlide>

        {/* Top cards */}
        <div style={{ display:'flex', gap:20, marginBottom:20 }}>
          <FadeSlide startFrame={S2_START+15} duration={15} direction="up" style={{ flex:1 }}>
            <Glass glow glowColor={theme.colors.purple}>
              <div style={{ fontSize:12,color:theme.colors.dim,fontFamily:fontFamily.mono,letterSpacing:2,textTransform:'uppercase',marginBottom:8 }}>Balance</div>
              <div style={{ display:'flex',alignItems:'baseline',gap:12 }}>
                <span style={{ fontSize:48,fontWeight:800,color:theme.colors.white,fontFamily:fontFamily.heading,fontVariantNumeric:'tabular-nums',textShadow:'0 0 30px rgba(153,69,255,0.3)' }}>
                  {balSOL}
                </span>
                <span style={{ fontSize:20,fontWeight:600,color:theme.colors.purple,fontFamily:fontFamily.heading }}>SOL</span>
              </div>
              <div style={{ fontSize:16,color:theme.colors.dim,fontFamily:fontFamily.mono,marginTop:4 }}>${balUSD}</div>
            </Glass>
          </FadeSlide>
          <FadeSlide startFrame={S2_START+25} duration={15} direction="up" style={{ flex:1 }}>
            <Glass glow glowColor={theme.colors.green}>
              <div style={{ fontSize:12,color:theme.colors.dim,fontFamily:fontFamily.mono,letterSpacing:2,textTransform:'uppercase',marginBottom:8 }}>24h Activity</div>
              <div style={{ display:'flex',gap:40,marginTop:12 }}>
                {[
                  { val:'47', label:'TXN COUNT', col:theme.colors.green },
                  { val:'0.4s', label:'AVG SETTLE', col:theme.colors.cyan },
                  { val:'100%', label:'SUCCESS', col:theme.colors.purpleLight },
                ].map((s,i) => (
                  <div key={i}>
                    <div style={{ fontSize:32,fontWeight:800,color:s.col,fontFamily:fontFamily.heading }}>{s.val}</div>
                    <div style={{ fontSize:11,color:theme.colors.dim,fontFamily:fontFamily.mono,letterSpacing:1 }}>{s.label}</div>
                  </div>
                ))}
              </div>
            </Glass>
          </FadeSlide>
        </div>

        {/* Transactions */}
        <FadeSlide startFrame={S2_START+35} duration={15} direction="up">
          <Glass style={{ padding:'16px 24px' }}>
            <div style={{ fontSize:12,color:theme.colors.dim,fontFamily:fontFamily.mono,letterSpacing:2,textTransform:'uppercase',marginBottom:14 }}>
              Recent Transactions
            </div>
            {txList.map((tx,i) => {
              const rd = S2_START+45+i*8;
              const ro = interpolate(frame,[rd,rd+10],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
              const rs = interpolate(frame,[rd,rd+10],[15,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
              return (
                <div key={i} style={{
                  display:'flex',justifyContent:'space-between',alignItems:'center',
                  padding:'10px 0', borderBottom:i<txList.length-1?'1px solid rgba(255,255,255,0.04)':'none',
                  opacity:ro, transform:`translateX(${rs}px)`,
                }}>
                  <div style={{ display:'flex',alignItems:'center',gap:12 }}>
                    <span style={{ fontSize:14,color:theme.colors.green,fontFamily:fontFamily.mono }}>✓</span>
                    <span style={{ fontSize:14,fontWeight:600,color:theme.colors.offWhite,fontFamily:fontFamily.heading }}>{tx.type}</span>
                    <span style={{ fontSize:12,color:theme.colors.dim,fontFamily:fontFamily.mono }}>→ {tx.to}</span>
                  </div>
                  <div style={{ display:'flex',alignItems:'center',gap:16 }}>
                    <span style={{
                      fontSize:14,fontWeight:700,fontFamily:fontFamily.mono,fontVariantNumeric:'tabular-nums',
                      color: tx.amt.startsWith('+')?theme.colors.green:theme.colors.offWhite,
                    }}>{tx.amt}</span>
                    <span style={{ fontSize:11,color:theme.colors.muted,fontFamily:fontFamily.mono }}>{tx.time}</span>
                  </div>
                </div>
              );
            })}
          </Glass>
        </FadeSlide>
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 3 — Live Transaction
   ═════════════════════════════════════════════════════════════ */
const txSteps = [
  { text:'Agent requesting 0.05 SOL transfer...', delay:0, icon:'🔄', color:theme.colors.cyan },
  { text:'Policy check: APPROVED', delay:50, icon:'✅', color:theme.colors.green },
  { text:'TX: 4sGjM...Kp2xR7vN', delay:90, icon:'📝', color:theme.colors.purple },
  { text:'solscan.io/tx/4sGjM...Kp2xR7vN', delay:120, icon:'🔗', color:theme.colors.cyan },
  { text:'Settled in 0.4s', delay:160, icon:'⚡', color:theme.colors.green },
];

const Scene3 = () => {
  const frame = useCurrentFrame();
  const lf = frame - S3_START;
  const fadeIn = interpolate(lf,[0,15],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const fadeOut = interpolate(lf,[S3_END-S3_START-20,S3_END-S3_START],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const prog = interpolate(lf,[0,50,90,160,180],[0,30,60,95,100],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const showSpd = lf >= 160;
  const spd = showSpd ? interpolate(lf,[160,190],[0,0.4],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}) : 0;

  return (
    <AbsoluteFill style={{ justifyContent:'center',alignItems:'center',opacity:fadeIn*fadeOut }}>
      <div style={{ width:800 }}>
        <FadeSlide startFrame={S3_START} duration={15} direction="up">
          <div style={{ textAlign:'center',marginBottom:40 }}>
            <div style={{ fontSize:14,fontWeight:600,color:theme.colors.purple,fontFamily:fontFamily.mono,letterSpacing:3,textTransform:'uppercase',marginBottom:8 }}>
              Live Transaction
            </div>
            <div style={{ fontSize:36,fontWeight:800,color:theme.colors.white,fontFamily:fontFamily.heading,textShadow:'0 0 30px rgba(153,69,255,0.3)' }}>
              Autonomous Transfer
            </div>
          </div>
        </FadeSlide>

        <FadeSlide startFrame={S3_START+10} duration={15} direction="up">
          <Glass glow glowColor={theme.colors.purple} style={{ padding:'32px 40px' }}>
            {/* Progress bar */}
            <div style={{ height:4,background:'rgba(255,255,255,0.06)',borderRadius:2,marginBottom:32,overflow:'hidden' }}>
              <div style={{
                height:'100%', width:`${prog}%`, borderRadius:2,
                background: prog>=95
                  ? `linear-gradient(90deg,${theme.colors.green},${theme.colors.cyan})`
                  : `linear-gradient(90deg,${theme.colors.purple},${theme.colors.cyan})`,
                boxShadow: `0 0 12px ${prog>=95?theme.colors.green:theme.colors.purple}60`,
              }} />
            </div>

            {txSteps.map((step,i) => {
              const se = lf - step.delay;
              if (se < 0) return null;
              const so = interpolate(se,[0,10],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
              const ss = interpolate(se,[0,10],[20,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
              return (
                <div key={i} style={{
                  display:'flex',alignItems:'center',gap:16,marginBottom:18,
                  opacity:so, transform:`translateX(${ss}px)`,
                }}>
                  <span style={{ fontSize:20 }}>{step.icon}</span>
                  <span style={{
                    fontSize:18,fontWeight:600,color:step.color,
                    fontFamily: step.text.includes('solscan')||step.text.includes('TX:')?fontFamily.mono:fontFamily.heading,
                    textShadow:`0 0 15px ${step.color}40`,
                  }}>{step.text}</span>
                </div>
              );
            })}

            {showSpd && (
              <div style={{
                marginTop:24,paddingTop:24,borderTop:'1px solid rgba(255,255,255,0.06)',
                display:'flex',justifyContent:'center',alignItems:'baseline',gap:8,
              }}>
                <span style={{
                  fontSize:64,fontWeight:900,color:theme.colors.green,fontFamily:fontFamily.heading,
                  fontVariantNumeric:'tabular-nums', textShadow:theme.glow.textGreen,
                }}>{spd.toFixed(1)}s</span>
                <span style={{ fontSize:16,color:theme.colors.dim,fontFamily:fontFamily.mono,letterSpacing:2 }}>
                  SETTLEMENT
                </span>
              </div>
            )}
          </Glass>
        </FadeSlide>
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 4 — Stats Counter
   ═════════════════════════════════════════════════════════════ */
const statItems = [
  { value:2847, label:'Agents Deployed', color:theme.colors.purple, fmt:v=>Math.round(v).toLocaleString() },
  { value:148293, label:'Transactions Settled', color:theme.colors.green, fmt:v=>Math.round(v).toLocaleString() },
  { value:4.2, label:'Total Volume', color:theme.colors.cyan, fmt:v=>'$'+v.toFixed(1)+'M', prefix:'$', suffix:'M' },
  { value:0.4, label:'Avg Settlement', color:theme.colors.purpleLight, fmt:v=>v.toFixed(1)+'s' },
];

const Scene4 = () => {
  const frame = useCurrentFrame();
  const lf = frame - S4_START;
  const fadeIn = interpolate(lf,[0,15],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const fadeOut = interpolate(lf,[S4_END-S4_START-20,S4_END-S4_START],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});

  return (
    <AbsoluteFill style={{ justifyContent:'center',alignItems:'center',opacity:fadeIn*fadeOut }}>
      <div style={{ width:'100%', maxWidth:1200, padding:'0 60px' }}>
        <FadeSlide startFrame={S4_START} duration={15} direction="up">
          <div style={{ textAlign:'center', marginBottom:60 }}>
            <div style={{ fontSize:14,fontWeight:600,color:theme.colors.green,fontFamily:fontFamily.mono,letterSpacing:3,textTransform:'uppercase',marginBottom:8 }}>
              Network Stats
            </div>
            <div style={{ fontSize:42,fontWeight:800,color:theme.colors.white,fontFamily:fontFamily.heading,textShadow:'0 0 30px rgba(153,69,255,0.3)' }}>
              Growing Every Day
            </div>
          </div>
        </FadeSlide>

        <div style={{ display:'flex', gap:24 }}>
          {statItems.map((stat,i) => {
            const delay = 15 + i*25;
            const el = lf - delay;
            if (el < 0) return <div key={i} style={{ flex:1,opacity:0 }} />;

            const rgb = hexToRgb(stat.color);
            const prog = easing.easeOutExpo(interpolate(el,[0,50],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}));
            const val = stat.value * prog;
            const disp = stat.fmt(val);
            const sc = easing.easeOutBack(interpolate(el,[0,20],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}));
            const op = interpolate(el,[0,10],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
            const pulse = 0.85+Math.sin((lf+i*20)*0.06)*0.15;

            return (
              <div key={i} style={{ flex:1, textAlign:'center', opacity:op, transform:`scale(${sc})` }}>
                <div style={{
                  background:`rgba(${rgb},0.04)`, border:`1px solid rgba(${rgb},0.12)`,
                  borderRadius:20, padding:'40px 20px', position:'relative', overflow:'hidden',
                }}>
                  {/* Top glow line */}
                  <div style={{
                    position:'absolute',top:0,left:'15%',right:'15%',height:1,
                    background:`linear-gradient(90deg,transparent,rgba(${rgb},0.3),transparent)`,
                  }} />
                  {/* Outer glow */}
                  <div style={{
                    position:'absolute',inset:-8,borderRadius:28,
                    background:`radial-gradient(ellipse,rgba(${rgb},${0.06*pulse}) 0%,transparent 70%)`,
                    filter:'blur(12px)', pointerEvents:'none',
                  }} />
                  <div style={{
                    fontSize:52,fontWeight:900,color:stat.color,fontFamily:fontFamily.heading,
                    fontVariantNumeric:'tabular-nums',
                    textShadow:`0 0 30px rgba(${rgb},0.4)`,
                    position:'relative',
                  }}>{disp}</div>
                  <div style={{
                    fontSize:12,color:theme.colors.dim,marginTop:12,letterSpacing:2.5,
                    textTransform:'uppercase',fontFamily:fontFamily.mono,position:'relative',
                  }}>{stat.label}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   SCENE 5 — CTA
   ═════════════════════════════════════════════════════════════ */
const Scene5 = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lf = frame - S5_START;
  const fadeIn = interpolate(lf,[0,15],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});

  const titleScale = spring({ frame, fps, delay:S5_START+10, config:{ damping:12, mass:1, stiffness:120 } });
  const titleOp = interpolate(lf,[8,25],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});

  const urlOp = interpolate(lf,[50,65],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const urlY = interpolate(lf,[50,65],[20,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});

  const pipOp = interpolate(lf,[80,95],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const pipY = interpolate(lf,[80,95],[20,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});

  const breathe = lf > 60 ? 0.8+Math.sin(lf*0.05)*0.2 : 1;

  const showParticles = lf >= 5;

  return (
    <AbsoluteFill style={{ justifyContent:'center',alignItems:'center',opacity:fadeIn }}>
      {/* Particle explosion on logo reveal — CSS particles to keep it light */}
      {showParticles && (
        <ParticleExplosion
          startFrame={S5_START+5}
          x="50%"
          y="45%"
          count={30}
          color={theme.colors.purple}
          secondaryColor={theme.colors.green}
          duration={40}
          spread={250}
        />
      )}

      <div style={{ textAlign:'center', position:'relative' }}>
        {/* Main title */}
        <div style={{ opacity:titleOp, transform:`scale(${titleScale})` }}>
          <GlitchText
            text="AgentWallet"
            startFrame={S5_START+10}
            color={theme.colors.white}
            fontSize={72}
            fontWeight={900}
            glitchIntensity={0.8}
            duration={20}
          />
        </div>
        <div style={{
          marginTop:12, opacity: interpolate(lf,[25,40],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),
          transform:`translateY(${interpolate(lf,[25,40],[10,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}px)`,
        }}>
          <span style={{
            fontSize:28,fontWeight:700,fontFamily:fontFamily.heading,
            background:`linear-gradient(90deg,${theme.colors.green},${theme.colors.cyan})`,
            WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent',
            letterSpacing:1,
          }}>
            is LIVE on Solana
          </span>
        </div>

        {/* Accent bar */}
        <div style={{
          width:120, height:3, margin:'28px auto',
          background:theme.gradients.accentBar,
          borderRadius:2,
          opacity: interpolate(lf,[40,55],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),
          boxShadow:`0 0 12px rgba(153,69,255,${0.3*breathe})`,
        }} />

        {/* URL */}
        <div style={{ opacity:urlOp, transform:`translateY(${urlY}px)` }}>
          <span style={{
            fontSize:32,fontWeight:800,color:theme.colors.purple,fontFamily:fontFamily.heading,
            textShadow:`0 0 30px rgba(153,69,255,${0.4*breathe})`,
            letterSpacing:1,
          }}>agentwallet.fun</span>
        </div>

        {/* pip install */}
        <div style={{ opacity:pipOp, transform:`translateY(${pipY}px)`, marginTop:24 }}>
          <div style={{
            display:'inline-block', background:'rgba(0,0,0,0.5)',
            border:'1px solid rgba(20,241,149,0.2)',
            borderRadius:8, padding:'12px 28px',
          }}>
            <span style={{
              fontSize:18, fontFamily:fontFamily.mono, color:theme.colors.green,
              textShadow:'0 0 10px rgba(20,241,149,0.3)', letterSpacing:0.5,
            }}>
              $ pip install agentwallet-mcp
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ═════════════════════════════════════════════════════════════
   MAIN COMPOSITION
   ═════════════════════════════════════════════════════════════ */
export const ProductDemo = () => {
  const frame = useCurrentFrame();

  return (
    <Background
      variant="default"
      showScanLine
      showParticles
      showGrid
      showVignette
      showNoise
      particleCount={20}
      vignetteIntensity={0.5}
    >
      {/* Scene 1: Terminal Boot (0-8s) */}
      {frame < S1_END && (
        <Sequence from={S1_START} durationInFrames={S1_END - S1_START}>
          <Scene1 />
        </Sequence>
      )}

      {/* Scene 2: Dashboard (8-20s) */}
      {frame >= S2_START - 5 && frame < S2_END && (
        <Sequence from={S2_START} durationInFrames={S2_END - S2_START}>
          <Scene2 />
        </Sequence>
      )}

      {/* Scene 3: Live Transaction (20-35s) */}
      {frame >= S3_START - 5 && frame < S3_END && (
        <Sequence from={S3_START} durationInFrames={S3_END - S3_START}>
          <Scene3 />
        </Sequence>
      )}

      {/* Scene 4: Stats (35-50s) */}
      {frame >= S4_START - 5 && frame < S4_END && (
        <Sequence from={S4_START} durationInFrames={S4_END - S4_START}>
          <Scene4 />
        </Sequence>
      )}

      {/* Scene 5: CTA (50-60s) */}
      {frame >= S5_START - 5 && (
        <Sequence from={S5_START} durationInFrames={S5_END - S5_START}>
          <Scene5 />
        </Sequence>
      )}
    </Background>
  );
};