# Manim example: transparent diagram clip

Tested with Manim Community v0.22.0 (Python 3.13).

    sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config python3-dev build-essential
    sudo apt-get install -y --no-install-recommends texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended dvisvgm   # only for MathTex
    python3 -m venv venv && venv/bin/pip install manim
    venv/bin/manim -t --format mov -qm diagram.py Funnel
    # -> media/videos/diagram/720p30/Funnel.mov (qtrle, alpha), 4 s

Composite over a video at 5.5 s with a dark scrim:

    ffmpeg -i base.mp4 -i media/videos/diagram/720p30/Funnel.mov -filter_complex \
      "[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.82:t=fill:enable='between(t,5.5,9.5)'[bg];\
       [1:v]scale=1600:-1,setpts=PTS-STARTPTS+5.5/TB[m];\
       [bg][m]overlay=(W-w)/2:(H-h)/2:eof_action=pass:enable='between(t,5.5,9.5)'[v]" \
      -map "[v]" -map 0:a -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a copy out.mp4
