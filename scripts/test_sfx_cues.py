import json
from pathlib import Path

import pytest

from sfx_cues import ASSET_DIR, load_sounds, plan_cues

FIXTURES = Path(__file__).parent / "fixtures" / "finish_pass"


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
