# yt-dlp-downloader skill (Claude Code + Cursor)

Paste a link and say "download this video", "extract the audio as mp3", "get
the 720p version with subtitles", or run `/yt-dlp-downloader <url> mp3`. The
agent runs `scripts/dl.py`, which wraps yt-dlp with resume, quality caps, MP3
extraction, subtitles and an automatic browser-cookie retry on YouTube 403s.

## Install

Clone this repo, then copy the skill folder into your skills directory:

```bash
git clone https://github.com/robert-awere/my-claude-skills
cd my-claude-skills

# Claude Code, all projects
mkdir -p ~/.claude/skills && cp -r skills/yt-dlp-downloader ~/.claude/skills/
# Claude Code, one project only (run from that project, adjust the source path)
mkdir -p .claude/skills && cp -r /path/to/my-claude-skills/skills/yt-dlp-downloader .claude/skills/
# Cursor
mkdir -p ~/.cursor/skills && cp -r skills/yt-dlp-downloader ~/.cursor/skills/
```

Install the tools once:

```bash
# macOS
brew install yt-dlp ffmpeg
# Windows
winget install yt-dlp.yt-dlp Gyan.FFmpeg
# Linux / pip
python3 -m pip install -U "yt-dlp[default]" && sudo apt install ffmpeg
```

Check it is loaded: type `/` in Claude Code and look for `yt-dlp-downloader`,
or ask "what skills are available?".

## Direct use (no agent)

```bash
python3 scripts/dl.py URL                 # best quality mp4
python3 scripts/dl.py URL -q 720          # cap at 720p
python3 scripts/dl.py URL -a              # mp3
python3 scripts/dl.py URL --subs en,ja    # + subtitles as .srt
python3 scripts/dl.py URL --browser chrome
python3 scripts/dl.py --help
```

Files land in `~/Downloads/yt-dlp` by default (`-o DIR` or `YTDLP_OUT=DIR`).
Interrupted? Re-run the same command; it resumes.

Note: Claude Code cloud sessions block most media hosts at the network layer,
so downloads only work there if the environment's network policy allows the
site. Local Claude Code has no such limit.
