# yt-dlp flags used by dl.py (verified against yt-dlp 2026.10.26 `--help`)

| dl.py option | yt-dlp flags |
|---|---|
| (always) | `--continue --no-overwrites --retries 10 --fragment-retries 10 --file-access-retries 5 --concurrent-fragments 4 --embed-metadata --no-mtime -P DIR -o "%(title).200B [%(id)s].%(ext)s" --no-playlist` |
| `-q N` | `-S "res:N,ext:mp4:m4a" --merge-output-format mp4` (best stream no taller than N px) |
| `-q best` | `-S "res,ext:mp4:m4a" --merge-output-format mp4` |
| `-a` | `-f "ba/b" -x --audio-format mp3 --audio-quality 0 --embed-thumbnail` (needs ffmpeg + ffprobe) |
| `--subs [LANGS]` | `--write-subs --sub-langs "en.*" --convert-subs srt` (LANGS is a comma list, regex allowed, `all` allowed, `-lang` excludes) |
| `--auto-subs` | `--write-auto-subs` |
| `--embed-subs` | `--embed-subs` (mp4/webm/mkv only) |
| `--playlist` | `--yes-playlist -o "%(playlist_title|)s/..."` |
| `--archive` | `--download-archive DIR/.archive.txt` |
| `--thumbnail` | `--embed-thumbnail` |
| `-N n` | `--concurrent-fragments n` |
| `--rate R` | `--limit-rate R` |
| `--browser B` | `--cookies-from-browser B` where B is `BROWSER[+KEYRING][:PROFILE][::CONTAINER]`; browsers: brave, chrome, chromium, edge, firefox, opera, safari, vivaldi, whale; Linux keyrings: basictext, gnomekeyring, kwallet, kwallet5, kwallet6 |
| `--cookies-file F` | `--cookies F` (Netscape format) |
| `--update` | `yt-dlp -U` for binaries, else `pip install -U "yt-dlp[default]"` |

Automatic cookie fallback triggers when yt-dlp's stderr contains any of:
`HTTP Error 403`, `Sign in to confirm`, `not a bot`, `login required`,
`Requested format is not available`, `use --cookies`, `Private video`,
`members-only`, `age-restricted`, `confirm your age`. It probes each installed
browser with `--cookies-from-browser B --simulate --print id URL` and re-runs the
download with the first one that works. Force a browser with `--browser` or
the `YTDLP_BROWSER` env var; disable with `--no-cookie-fallback`.

Useful raw yt-dlp commands if you need to go beyond the script:

```bash
yt-dlp -F URL                                  # list formats
yt-dlp --list-subs URL                         # list subtitle languages
yt-dlp -t mp3 URL                              # built-in preset alias (= -x --audio-format mp3)
yt-dlp -t mp4 URL                              # built-in preset alias for h264 mp4
yt-dlp --extractor-args "youtube:player_client=default,-web" URL   # try other YT clients
yt-dlp --js-runtimes node URL                  # use node instead of deno for YT challenges
yt-dlp --download-sections "*00:01:00-00:02:30" URL   # clip a section (needs ffmpeg)
```

Docs: https://github.com/yt-dlp/yt-dlp#usage-and-options
