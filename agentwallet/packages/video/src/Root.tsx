import { Composition } from "remotion";
import Launch from "./Launch";

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
    </>
  );
};
