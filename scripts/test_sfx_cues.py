import json
from pathlib import Path

import pytest

from sfx_cues import ASSET_DIR, cut_times, load_sounds, plan_cues

FIXTURES = Path(__file__).parent / "fixtures" / "finish_pass"


@pytest.mark.parametrize("contents", ["", "\nStart Time (seconds)\n", "  \n"])
def test_scene_csv_requires_first_row(tmp_path, contents):
    scenes = tmp_path / "scenes.csv"
    scenes.write_text(contents)
    with pytest.raises(ValueError, match="scene CSV needs a non-blank first row"):
        cut_times(None, scenes)


def test_bundled_audio_is_verified():
    sounds = load_sounds()
    assert set(sounds) == {"click", "latch", "whoosh", "riser", "impact"}
    assert {s.file for s in sounds.values()} == {p.name for p in ASSET_DIR.glob("*.wav")}


@pytest.mark.parametrize("field,value", [("license", "CC-BY-4.0"), ("sha256", "0" * 64)])
def test_modified_manifest_is_refused(tmp_path, field, value):
    import shutil

    shutil.copytree(ASSET_DIR, tmp_path / "sfx")
    manifest = tmp_path / "sfx" / "manifest.json"
    data = json.loads(manifest.read_text())
    data["sounds"][0][field] = value
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=field):
        load_sounds(manifest.parent)


def test_reproduces_signal_reference():
    events = json.loads((FIXTURES / "signal_cue_events.json").read_text())
    reference = json.loads((FIXTURES / "signal_cues_reference.json").read_text())["cues"]
    cues = plan_cues(**events)
    assert len(cues) == len(reference) == 23
    for found, expected in zip(cues, reference):
        assert found.sound == expected["sound"]
        assert found.time == pytest.approx(expected["time"], abs=1 / 30)
        assert found.gain_db == expected["gain_db"]


def test_license_table_matches_manifest():
    notice = (ASSET_DIR / "LICENSES.md").read_text()
    manifest = json.loads((ASSET_DIR / "manifest.json").read_text())
    assert "CC0-1.0" in notice
    for sound in manifest["sounds"]:
        assert sound["license"] == "CC0-1.0"
        assert sound["file"] in notice
        assert sound["sha256"] in notice


def test_changed_wav_is_refused(tmp_path):
    import shutil

    library = tmp_path / "sfx"
    shutil.copytree(ASSET_DIR, library)
    wav = library / "cgai_click_v1.wav"
    wav.write_bytes(wav.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="sha256"):
        load_sounds(library)


@pytest.mark.parametrize("variable", [False, True])
def test_motion_and_cut_strength_follow_presentation_time(tmp_path, variable):
    from sfx_cues import cue_events, ffmpeg

    clip = tmp_path / "motion.mp4"
    timing = "setpts='if(lt(N,6),15*N,N+84)'," if variable else ""
    ffmpeg("-v", "error", "-f", "lavfi", "-i", "color=black:s=96x96:r=30:d=9",
           "-vf", timing + "drawbox=c=white:t=fill:enable='gte(t,2)'",
           "-fps_mode", "passthrough", "-c:v", "libx264", "-output_ts_offset", "0.375", clip)
    scenes = tmp_path / "scenes.csv"
    scenes.write_text("Timecode List:\n")
    events = cue_events(clip, 9, 30, scenes)
    clicks = [cue.time for cue in plan_cues(**events) if cue.sound == "click"]
    assert clicks == [pytest.approx(2, abs=1/30)]

    scenes.write_text("Timecode List:,00:00:01.990\n")
    events = cue_events(clip, 9, 30, scenes)
    assert events["cuts"][0][1] > 200


def test_motion_analysis_rejects_timestamp_count_mismatch(monkeypatch):
    import sfx_cues

    monkeypatch.setattr(sfx_cues, "cut_times", lambda *args: [])
    monkeypatch.setattr(sfx_cues, "motion_deltas", lambda *args: [0, 1, 0])
    monkeypatch.setattr(sfx_cues, "frame_times", lambda *args: [0, 0.5], raising=False)
    with pytest.raises(ValueError, match="decoded 3 frames but found 2 frame timestamps"):
        sfx_cues.cue_events(None, 1, 30)
