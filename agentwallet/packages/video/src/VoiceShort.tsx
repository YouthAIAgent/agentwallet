import { Audio, Sequence } from "remotion";
import v_s15_00 from "../voice/s15-00.mp3";
import v_s15_01 from "../voice/s15-01.mp3";
import v_s15_02 from "../voice/s15-02.mp3";
import v_s15_03 from "../voice/s15-03.mp3";
import v_s15_04 from "../voice/s15-04.mp3";

export function VoiceShort15() {
  return (
    <>
      <Sequence from={15}>
        <Audio src={v_s15_00} />
      </Sequence>
      <Sequence from={90}>
        <Audio src={v_s15_01} />
      </Sequence>
      <Sequence from={178}>
        <Audio src={v_s15_02} />
      </Sequence>
      <Sequence from={269}>
        <Audio src={v_s15_03} />
      </Sequence>
      <Sequence from={381}>
        <Audio src={v_s15_04} />
      </Sequence>
    </>
  );
}


import { Audio, Sequence } from "remotion";
import v_s30_00 from "../voice/s30-00.mp3";
import v_s30_01 from "../voice/s30-01.mp3";
import v_s30_02 from "../voice/s30-02.mp3";
import v_s30_03 from "../voice/s30-03.mp3";
import v_s30_04 from "../voice/s30-04.mp3";
import v_s30_05 from "../voice/s30-05.mp3";
import v_s30_06 from "../voice/s30-06.mp3";
import v_s30_07 from "../voice/s30-07.mp3";
import v_s30_08 from "../voice/s30-08.mp3";

export function VoiceShort30() {
  return (
    <>
      <Sequence from={15}>
        <Audio src={v_s30_00} />
      </Sequence>
      <Sequence from={102}>
        <Audio src={v_s30_01} />
      </Sequence>
      <Sequence from={175}>
        <Audio src={v_s30_02} />
      </Sequence>
      <Sequence from={266}>
        <Audio src={v_s30_03} />
      </Sequence>
      <Sequence from={334}>
        <Audio src={v_s30_04} />
      </Sequence>
      <Sequence from={414}>
        <Audio src={v_s30_05} />
      </Sequence>
      <Sequence from={565}>
        <Audio src={v_s30_06} />
      </Sequence>
      <Sequence from={647}>
        <Audio src={v_s30_07} />
      </Sequence>
      <Sequence from={827}>
        <Audio src={v_s30_08} />
      </Sequence>
    </>
  );
}
