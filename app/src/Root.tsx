import { Composition } from "remotion";
import { FacelessShort } from "./FacelessShort";
import facelessPlan from "../public/faceless-plan.json";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="FacelessShort"
        component={FacelessShort as any}
        durationInFrames={facelessPlan.totalDurationInFrames}
        fps={facelessPlan.fps}
        width={facelessPlan.width}
        height={facelessPlan.height}
        defaultProps={{ plan: facelessPlan as any }}
      />
    </>
  );
};
