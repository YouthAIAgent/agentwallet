import { Audio, Sequence } from "remotion";
import v00 from "../voice/mo-00.mp3";
import v01 from "../voice/mo-01.mp3";
import v02 from "../voice/mo-02.mp3";
import v03 from "../voice/mo-03.mp3";
import v04 from "../voice/mo-04.mp3";
import v05 from "../voice/mo-05.mp3";
import v06 from "../voice/mo-06.mp3";
import v07 from "../voice/mo-07.mp3";
import v08 from "../voice/mo-08.mp3";
import v09 from "../voice/mo-09.mp3";

export function VoiceMograph() {
  return (
    <>
      <Sequence from={0}>
        <Audio src={v00} />
      </Sequence>
      <Sequence from={150}>
        <Audio src={v01} />
      </Sequence>
      <Sequence from={330}>
        <Audio src={v02} />
      </Sequence>
      <Sequence from={557}>
        <Audio src={v03} />
      </Sequence>
      <Sequence from={750}>
        <Audio src={v04} />
      </Sequence>
      <Sequence from={960}>
        <Audio src={v05} />
      </Sequence>
      <Sequence from={1207}>
        <Audio src={v06} />
      </Sequence>
      <Sequence from={1380}>
        <Audio src={v07} />
      </Sequence>
      <Sequence from={1590}>
        <Audio src={v08} />
      </Sequence>
      <Sequence from={1800}>
        <Audio src={v09} />
      </Sequence>
    </>
  );
}
