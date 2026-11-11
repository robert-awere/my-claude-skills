---
name: yt-dlp-downloader
description: Download video or audio from a URL (YouTube, Bilibili, X/Twitter, TikTok, Vimeo, Reddit, Instagram and 1000+ other sites) with yt-dlp. Use when the user pastes a media link and asks to download it, save it, grab the audio/MP3, get subtitles, pick a quality (720p/1080p/best), or resume a broken download. Handles YouTube 403 / "sign in to confirm you're not a bot" by retrying with the user's browser cookies.
argument-hint: "<url> [mp3 | 720 | 1080 | best | subs]"
---

# yt-dlp downloader

Run everything through the helper script that ships in this skill's folder. It
wraps `yt-dlp` with sane defaults, resume + retries, MP3 extraction, subtitles,
a quality cap, and an automatic browser-cookie retry when a site returns 403 or
asks for a login.

```bash
python3 "<skill-dir>/scripts/dl.py" <URL> [options]
```

`<skill-dir>` is the directory containing this SKILL.md. In Claude Code it is
`${CLAUDE_SKILL_DIR}`. Typical locations:

- project skill: `.claude/skills/yt-dlp-downloader` (Claude Code; Cursor reads it too)
- personal skill: `~/.claude/skills/yt-dlp-downloader` or `~/.cursor/skills/yt-dlp-downloader`

On Windows use `python` instead of `python3`. Shown below as `dl.py` for brevity.

If the skill was invoked with arguments (`/yt-dlp-downloader URL mp3`), treat
them as the URL plus a plain-language request and map them with the table below.

## Map the request to flags

| User says | Run |
|---|---|
| "download this video" | `dl.py URL` (best quality, mp4) |
| "in 720p" / "1080p" / "best" | `dl.py URL -q 720` / `-q 1080` / `-q best` |
| "just the audio", "as mp3", "extract the audio" | `dl.py URL -a` |
| "with subtitles" / "captions" | `dl.py URL --subs` (English .srt next to the video) |
| "Japanese and English subs" | `dl.py URL --subs ja,en` |
| "burn in / embed the subtitles" | `dl.py URL --subs --embed-subs` |
| "auto-generated captions are fine" | add `--auto-subs` |
| "the whole playlist / channel" | add `--playlist --archive` |
| "save it to ~/Movies" | add `-o ~/Movies` |
| "use my Firefox login" | add `--browser firefox` |
| "it stopped halfway, continue it" | re-run the exact same command (resume is automatic) |
| "update yt-dlp" | `dl.py --update` |

Several URLs can be passed at once. Anything after a literal `--` is forwarded to
yt-dlp unchanged, e.g. `dl.py URL -- --proxy socks5://127.0.0.1:1080`.

Default output folder: `~/Downloads/yt-dlp` (override with `-o DIR` or the
`YTDLP_OUT` env var). Filenames are `Title [id].ext`.

## Workflow

1. Run `dl.py --dry-run URL ...` only if you are unsure which flags apply;
   otherwise run the real command directly. Show the user the command.
2. Let it run in the terminal. The script prints yt-dlp's progress live.
3. When it finishes, report the output path(s) (the last `[download] Destination`
   / `[Merger]` / `[ExtractAudio]` line names the file). Do not open or play files.
4. If it fails, read the error and apply the fixes below. Re-run once; do not
   loop more than twice without telling the user what is wrong.

## Error handling

- **403 / "Sign in to confirm you're not a bot" / "login required" / private or
  age-restricted**: the script already retries automatically with cookies from
  the installed browsers (chrome, safari, firefox, brave, edge, ...). If it still
  fails: ask the user to log in to the site in their browser, close Chrome/Edge
  (they lock the cookie database while open), and re-run with
  `--browser chrome` (or `firefox`, `safari`, ...). As a last resort they can
  export a `cookies.txt` with a browser extension and pass `--cookies-file`.
- **"Unable to connect to proxy" / "Tunnel connection failed: 403"**: the
  machine's own network policy is blocking the media host (typical in Claude
  Code cloud sessions). This is not a site 403 and cookies will not help. Tell
  the user to run it in local Claude Code or allow the host in the environment's
  network settings.
- **"yt-dlp not found"** / **"ffmpeg not found"**: install per the Setup
  section, then re-run.
- **"Requested format is not available"** or weird YouTube failures on an old
  install: run `dl.py --update` first. yt-dlp needs updating often because sites
  change; most YouTube breakage is fixed by updating.
- **YouTube asks for a JavaScript runtime** (message mentions `deno` /
  `--js-runtimes`): install Deno (`brew install deno`, `winget install
  DenoLand.Deno`, or `curl -fsSL https://deno.land/install.sh | sh`) and make sure
  yt-dlp was installed as `yt-dlp[default]` so the `yt-dlp-ejs` helper is present.
- **Interrupted download**: just re-run the same command. `--continue` resumes
  `.part` files and fragments; `--no-overwrites` skips files already finished.
- **Rate-limited / "Too many requests"**: add `--rate 2M` or
  `-- --sleep-requests 1`.
- **Geo-blocked**: forward a proxy, e.g. `-- --proxy http://host:port`.

## Setup (one-time)

Required: Python 3.11+, `yt-dlp`, `ffmpeg` + `ffprobe` on PATH.

```bash
# macOS
brew install yt-dlp ffmpeg deno
# Windows (PowerShell)
winget install yt-dlp.yt-dlp Gyan.FFmpeg DenoLand.Deno
# Linux / any OS with Python
python3 -m pip install -U "yt-dlp[default]"   # plus: sudo apt install ffmpeg
```

Check with `yt-dlp --version` and `ffmpeg -version`. Deno is only needed for
YouTube's newer signature challenges; skip it until yt-dlp asks for it.

## Notes for the agent

- Never pass `-f`/`-S` yourself; use `-q`. The script picks
  `bv*+ba/b` sorted by `res:<N>` and merges to mp4.
- `-a` produces MP3 at ffmpeg VBR quality 0 with cover art; use
  `--audio-quality 192K` for a fixed bitrate if asked.
- `--subs` writes `.srt`; `--embed-subs` additionally muxes them into the mp4.
- Only download content the user has the right to download. Do not help bypass
  DRM; yt-dlp cannot and this skill will not.
- See `reference.md` for the raw yt-dlp flags behind each option.
