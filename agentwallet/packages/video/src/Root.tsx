import { Composition } from "remotion";
import Launch from "./Launch";
import { Mograph } from "./Mograph";
import { Short15, Short30 } from "./Shorts";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="AgentWalletLaunch"
        component={Launch}
        durationInFrames={3600}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="AgentWalletMograph"
        component={Mograph}
        durationInFrames={2040}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="AgentWalletShort15"
        component={Short15}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="AgentWalletShort30"
        component={Short30}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
