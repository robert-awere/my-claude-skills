# my-claude-skills
a collection of my own created claude skills

## Skills

| Skill | What it does |
|---|---|
| [yt-dlp-downloader](skills/yt-dlp-downloader) | Download video, MP3 audio and subtitles from YouTube, Bilibili, X, TikTok and other yt-dlp sites. Quality cap, resume, automatic browser-cookie retry on 403. |

## Install a skill

```bash
git clone https://github.com/robert-awere/my-claude-skills
mkdir -p ~/.claude/skills && cp -r my-claude-skills/skills/<skill-name> ~/.claude/skills/
```

Claude Code picks it up on the next start. Invoke with `/<skill-name>` or just describe the task.
