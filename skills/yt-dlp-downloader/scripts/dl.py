#!/usr/bin/env python3
"""dl.py - thin, opinionated wrapper around yt-dlp.

Features
  * video download at a chosen quality cap (720p / 1080p / best)
  * audio-only extraction to MP3 (-a)
  * subtitles (--subs [langs]), auto-generated subs, embedding
  * resume of interrupted downloads (yt-dlp --continue, retries)
  * automatic browser-cookie fallback when a site answers 403 /
    "Sign in to confirm you're not a bot" / login required
  * works on macOS, Linux and Windows; needs yt-dlp + ffmpeg on PATH

Examples
  dl.py URL                       # best quality video (mp4)
  dl.py URL -q 720                # cap at 720p
  dl.py URL -a                    # mp3 audio only
  dl.py URL --subs                # video + English subtitles (.srt)
  dl.py URL --subs en,ja --embed-subs
  dl.py URL --browser firefox     # force cookies from Firefox
  dl.py --update                  # update yt-dlp itself
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import threading
from pathlib import Path

QUALITIES = ["best", "2160", "1440", "1080", "720", "480", "360"]
BROWSERS_BY_OS = {
    "Darwin": ["chrome", "safari", "firefox", "brave", "edge", "chromium", "vivaldi", "opera"],
    "Windows": ["chrome", "firefox", "edge", "brave", "chromium", "vivaldi", "opera"],
    "Linux": ["chrome", "firefox", "brave", "chromium", "edge", "vivaldi", "opera"],
}
# Substrings (lower-cased) in yt-dlp's stderr that mean "retry with cookies".
AUTH_HINTS = (
    "http error 403",
    "sign in to confirm",
    "not a bot",
    "login required",
    "requested format is not available",  # frequent symptom of a blocked client
    "use --cookies",
    "cookies-from-browser",
    "private video",
    "members-only",
    "age-restricted",
    "confirm your age",
    "this video is only available for registered users",
)
DEFAULT_OUT = Path(os.environ.get("YTDLP_OUT", Path.home() / "Downloads" / "yt-dlp"))


# --------------------------------------------------------------------------- #
# tooling checks
# --------------------------------------------------------------------------- #
def ytdlp_cmd() -> list[str]:
    """Return the command prefix used to invoke yt-dlp."""
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    try:
        import yt_dlp  # noqa: F401
        return [sys.executable, "-m", "yt_dlp"]
    except ImportError:
        pass
    sys.exit(
        "yt-dlp not found.\n"
        "  install:  python3 -m pip install -U \"yt-dlp[default]\"\n"
        "  or:       brew install yt-dlp      (macOS)\n"
        "  or:       winget install yt-dlp.yt-dlp   (Windows)\n"
        "  or grab the binary from https://github.com/yt-dlp/yt-dlp/releases"
    )


def check_ffmpeg(required: bool) -> bool:
    ok = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
    if not ok:
        msg = (
            "ffmpeg/ffprobe not found on PATH. Needed for MP3 extraction, merging "
            "video+audio and embedding subs/thumbnails.\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt install ffmpeg\n"
            "  Windows: winget install Gyan.FFmpeg   (then reopen the terminal)"
        )
        if required:
            sys.exit(msg)
        print("warning: " + msg, file=sys.stderr)
    return ok


def update_ytdlp() -> int:
    exe = shutil.which("yt-dlp")
    if exe and not exe.lower().endswith((".py",)):
        # Try the self-updater first (works for standalone binaries).
        rc = subprocess.call([exe, "-U"])
        if rc == 0:
            return 0
    return subprocess.call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp[default]"])


# --------------------------------------------------------------------------- #
# command construction
# --------------------------------------------------------------------------- #
def build_args(a: argparse.Namespace) -> list[str]:
    out_dir = Path(a.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    args: list[str] = [
        "--continue",            # resume .part files / fragments (default, but explicit)
        "--no-overwrites",       # never clobber a finished file; rerun = resume or skip
        "--retries", "10",
        "--fragment-retries", "10",
        "--file-access-retries", "5",
        "--concurrent-fragments", str(a.threads),
        "--embed-metadata",
        "--no-mtime",
        "-P", str(out_dir),
    ]
    if a.playlist:
        args += ["--yes-playlist", "-o", "%(playlist_title|)s/" + a.template]
    else:
        args += ["--no-playlist", "-o", a.template]
    if a.archive:
        args += ["--download-archive", str(out_dir / ".archive.txt")]

    if a.audio:
        args += [
            "-f", "ba/b",                 # best audio, else best combined
            "-x", "--audio-format", "mp3",
            "--audio-quality", a.audio_quality,
            "--embed-thumbnail",
        ]
    else:
        args += ["--merge-output-format", "mp4"]
        if a.quality != "best":
            # prefer the best stream <= N pixels tall (yt-dlp -S res:N semantics)
            args += ["-S", f"res:{a.quality},ext:mp4:m4a"]
        else:
            args += ["-S", "res,ext:mp4:m4a"]
        if a.thumbnail:
            args += ["--embed-thumbnail"]

    if a.subs is not None:
        langs = a.subs or "en.*"
        args += ["--write-subs", "--sub-langs", langs, "--convert-subs", "srt"]
        if a.auto_subs:
            args += ["--write-auto-subs"]
        if a.embed_subs and not a.audio:
            args += ["--embed-subs"]

    if a.cookies_file:
        args += ["--cookies", str(Path(a.cookies_file).expanduser())]
    if a.rate:
        args += ["--limit-rate", a.rate]
    if a.extra:
        args += a.extra
    return args


# --------------------------------------------------------------------------- #
# running
# --------------------------------------------------------------------------- #
def run(cmd: list[str], quiet: bool = False) -> tuple[int, str]:
    """Run yt-dlp. Progress goes straight to the terminal (stdout); stderr is
    mirrored to the terminal and captured so we can inspect error text."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    captured: list[str] = []

    def pump() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            captured.append(line)
            if not quiet:
                sys.stderr.write(line)
                sys.stderr.flush()

    t = threading.Thread(target=pump, daemon=True)
    t.start()
    rc = proc.wait()
    t.join()
    return rc, "".join(captured)


def looks_like_auth_error(stderr: str) -> bool:
    s = stderr.lower()
    return any(h in s for h in AUTH_HINTS)


def browser_candidates(forced: str | None) -> list[str]:
    if forced:
        return [forced]
    env = os.environ.get("YTDLP_BROWSER")
    if env:
        return [env]
    return BROWSERS_BY_OS.get(platform.system(), BROWSERS_BY_OS["Linux"])


def probe_browser(base: list[str], browser: str, url: str) -> bool:
    """Cheap check: can yt-dlp read this browser's cookies and fetch metadata?"""
    cmd = base + [
        "--cookies-from-browser", browser,
        "--simulate", "--no-playlist", "--quiet", "--no-warnings",
        "--print", "id", url,
    ]
    try:
        rc = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
    except subprocess.TimeoutExpired:
        return False
    return rc == 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="dl.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("urls", nargs="*", help="one or more video/page URLs")
    p.add_argument("-a", "--audio", action="store_true", help="extract audio only, as MP3")
    p.add_argument("-q", "--quality", default="best", choices=QUALITIES,
                   help="max video height (default: best)")
    p.add_argument("--audio-quality", default="0",
                   help="ffmpeg VBR 0 (best) .. 10, or bitrate like 192K (default 0)")
    p.add_argument("-s", "--subs", nargs="?", const="", metavar="LANGS",
                   help="download subtitles; optional comma list e.g. en,ja (default en.*)")
    p.add_argument("--auto-subs", action="store_true",
                   help="also accept auto-generated subtitles")
    p.add_argument("--embed-subs", action="store_true",
                   help="embed subtitles into the video file as well")
    p.add_argument("-o", "--out", default=str(DEFAULT_OUT),
                   help=f"output folder (default {DEFAULT_OUT}; env YTDLP_OUT)")
    p.add_argument("--template", default="%(title).200B [%(id)s].%(ext)s",
                   help="yt-dlp output template")
    p.add_argument("--playlist", action="store_true",
                   help="download the whole playlist (default: single video only)")
    p.add_argument("--archive", action="store_true",
                   help="record downloaded IDs so reruns skip finished items")
    p.add_argument("--thumbnail", action="store_true", help="embed thumbnail into video")
    p.add_argument("-N", "--threads", type=int, default=4,
                   help="concurrent fragments for HLS/DASH (default 4)")
    p.add_argument("--rate", metavar="RATE", help="limit rate, e.g. 5M")
    p.add_argument("-b", "--browser", metavar="BROWSER",
                   help="use cookies from this browser from the start "
                        "(chrome, firefox, edge, brave, chromium, safari, vivaldi, opera, whale; "
                        "supports yt-dlp's BROWSER[+KEYRING][:PROFILE][::CONTAINER] syntax)")
    p.add_argument("--cookies-file", metavar="FILE", help="Netscape cookies.txt to use")
    p.add_argument("--no-cookie-fallback", action="store_true",
                   help="do not try browser cookies automatically after a 403/login error")
    p.add_argument("--dry-run", action="store_true", help="print the yt-dlp command and exit")
    p.add_argument("--update", action="store_true", help="update yt-dlp and exit")
    p.epilog = "Anything after a literal '--' is passed straight to yt-dlp."
    argv = list(sys.argv[1:] if argv is None else argv)
    extra: list[str] = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    a = p.parse_args(argv)
    a.extra = extra

    if a.update:
        return update_ytdlp()
    if not a.urls:
        p.error("at least one URL is required")

    base = ytdlp_cmd()
    check_ffmpeg(required=a.audio or bool(a.embed_subs))
    common = build_args(a)

    rc_total = 0
    for url in a.urls:
        cmd = base + common
        if a.browser:
            cmd += ["--cookies-from-browser", a.browser]
        cmd += [url]

        if a.dry_run:
            print(subprocess.list2cmdline(cmd))
            continue

        print(f"\n==> {url}", flush=True)
        rc, err = run(cmd)
        if rc == 0:
            continue

        if a.browser or a.cookies_file or a.no_cookie_fallback or not looks_like_auth_error(err):
            rc_total = rc
            continue

        # ---- automatic cookie fallback -------------------------------------
        print("\n!! Site refused the request (403 / login / bot check). "
              "Retrying with browser cookies...", file=sys.stderr)
        used = None
        for b in browser_candidates(None):
            print(f"   trying cookies from {b} ...", file=sys.stderr)
            if probe_browser(base, b, url):
                used = b
                break
        if not used:
            print("   no usable browser cookies found. Log in to the site in your browser, "
                  "close it (Chrome/Edge lock the cookie DB while open), then rerun with "
                  "--browser <name>, or export cookies.txt and pass --cookies-file.",
                  file=sys.stderr)
            rc_total = rc
            continue
        print(f"   using cookies from {used}", file=sys.stderr)
        rc, _ = run(base + common + ["--cookies-from-browser", used, url])
        rc_total = rc or rc_total

    return rc_total


if __name__ == "__main__":
    sys.exit(main())
