# Storyboard example (pattern only)

Production boards stay with the job (not in this repo). See `references/storyboard.md` for the required fields and HTML craft bar.

Minimal shape the edit builder expects in `storyboard.json`:

```json
{
  "runtime": 45.0,
  "pdf": [["OPEN", 0, 5, "beat description", "VO line"]],
  "shots": [
    {
      "id": "01",
      "act": "I",
      "beat": "OPEN",
      "t0": 0.0,
      "t1": 0.7,
      "picture": "Black.",
      "src": ["render", 0.3],
      "words": "",
      "voice": "",
      "audio": "Faint pulse.",
      "intent": "Silence before the idea.",
      "status": "HAVE",
      "serves": "Black · pulse"
    }
  ]
}
```

Generate a human HTML view (timeline + shot cards + HAVE/ID/NEED/TEMP chips) from that JSON before long renders. Status chips replace grey “FOOTAGE TBD” cards.

## This folder

`storyboard.json` and `storyboard.html` are a fictional 45s Harbor Atelier board: dense beats, a kinetic recipe on type shots, all four statuses, one named spectacle (shot 05), a breather (shot 07), and a door callback. Nothing here is client media. NEED and TEMP are on the board and marked to stay out of a client draft. ID waits for a yes. Open the HTML in a browser; it does not fetch the JSON.
