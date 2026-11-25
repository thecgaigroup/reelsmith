# SFX licenses

These original synthesized sounds are dedicated under [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/). The prototype generator was `patch/new/scripts/sfx_cues.py` in the finish-pass proof. It used NumPy PCG64 seed 20261125, 48 kHz mono PCM16, synth order click, latch, whoosh, riser, impact, and -3 dBFS peaks except for the impact. It used no third-party samples.

| File | Synthesis parameters | SHA-256 |
|---|---|---|
| `cgai_click_v1.wav` | 35 ms, noise high-passed at 2.5 kHz, 0.5 ms attack and 12 ms decay plus a 3.2 kHz sine ping | `b03d8b3eb0c4f6daf8c0eab11f4492db58487ed13e3e28deb1c673a2102155bd` |
| `cgai_latch_v1.wav` | 125 ms, two clicks 55 ms apart, second at 0.7 amplitude, with a decaying 180 Hz sine | `02902d3953a9d6105910e4a3739c046ab81979cfc6e33083079566b8b75c24a7` |
| `cgai_whoosh_v1.wav` | 550 ms, filtered noise swept from 300 Hz to 5.5 kHz and back, 120 Hz high-pass, sine-squared swell | `57cb1f6f2d114403f50642a3b613ace9a5d1ec95c0e8913207036042fec9b803` |
| `cgai_riser_v1.wav` | 1.2 s, 220–880 Hz exponential sweep plus its second harmonic and 3 kHz high-passed noise, power envelope 2.2 | `c30bdcb16968fac271a9101973056724126ae719125e58207cc11ef5417faf96` |
| `cgai_impact_v1.wav` | 1.6 s, pitch falls from 108 Hz toward 38 Hz, low-passed crack at 1.8 kHz and tail at 900 Hz, peak -1 dBFS | `754dedf2cbb9bee702164a69a565fdca7c806b05573c4a60e5b8b80ffa52939c` |
