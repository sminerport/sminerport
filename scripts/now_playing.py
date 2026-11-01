#!/usr/bin/env python3
"""Render a "now playing / recently played" card from Last.fm as a static SVG.

Run by .github/workflows/now-playing.yml, which publishes the result to the
`output` branch so the profile README can embed it without any live server.

    LASTFM_API_KEY=... python3 scripts/now_playing.py --user ScottDataScienc --out dist/now-playing.svg
    python3 scripts/now_playing.py --sample --out /tmp/sample.svg   # render without hitting the API
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

API = "https://ws.audioscrobbler.com/2.0/"
USER_AGENT = "sminerport-profile-now-playing/1.0 (+https://github.com/sminerport/sminerport)"
PLACEHOLDER_ART = "2a96cbd8b46e442fc41c2b86b821562f"  # Last.fm's "no artwork" image

# Card geometry (CSS pixels).
WIDTH, HEIGHT = 480, 132
PAD = 16
ART = HEIGHT - 2 * PAD
TEXT_X = PAD + ART + PAD
TEXT_W = WIDTH - TEXT_X - PAD

BG, FG, MUTED, ACCENT, RULE = "#212121", "#ffffff", "#b3b3b3", "#1db954", "#333333"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def latest_track(user, api_key):
    """Return the newest scrobble (or the track playing right now) as a dict, or None."""
    query = urllib.parse.urlencode(
        {"method": "user.getrecenttracks", "user": user, "api_key": api_key, "format": "json", "limit": 1}
    )
    try:
        body = fetch(f"{API}?{query}")
    except urllib.error.HTTPError as exc:
        body = exc.read()  # Last.fm sends its error JSON with a 4xx status
    data = json.loads(body)
    if "error" in data:
        raise RuntimeError(f"Last.fm error {data['error']}: {data.get('message')}")
    tracks = data["recenttracks"].get("track", [])
    if isinstance(tracks, dict):  # Last.fm returns a bare object when there is exactly one
        tracks = [tracks]
    if not tracks:
        return None
    t = tracks[0]
    images = {img["size"]: img["#text"] for img in t.get("image", [])}
    art = images.get("large") or images.get("extralarge") or ""
    if PLACEHOLDER_ART in art:
        art = ""
    return {
        "name": t.get("name", ""),
        "artist": t.get("artist", {}).get("#text", ""),
        "album": t.get("album", {}).get("#text", ""),
        "url": t.get("url", ""),
        "now_playing": t.get("@attr", {}).get("nowplaying") == "true",
        "art_url": art,
    }


def art_data_uri(url):
    """Download album art and return it as a data: URI, or None on any failure."""
    if not url:
        return None
    try:
        raw = fetch(url)
    except Exception as exc:  # noqa: BLE001 - artwork is optional
        print(f"warning: could not fetch artwork: {exc}", file=sys.stderr)
        return None
    if raw.startswith(b"\x89PNG"):
        mime = "image/png"
    elif raw.startswith(b"\xff\xd8"):
        mime = "image/jpeg"
    elif raw.startswith(b"GIF8"):
        mime = "image/gif"
    elif raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return None
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def clip(text, max_chars):
    text = " ".join(text.split())
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"


def equalizer(now_playing, x, y, width, bar_w=3, gap=3, height=22):
    """Rows of bars under the text. Animated while something is playing, idle otherwise."""
    bars = []
    count = width // (bar_w + gap)
    for i in range(count):
        bx = x + i * (bar_w + gap)
        # Deterministic variety so the card looks lively without being noisy.
        duration = 600 + (i * 137) % 700
        delay = (i * 89) % 500
        style = f"animation-duration:{duration}ms;animation-delay:-{delay}ms" if now_playing else ""
        bars.append(
            f'<rect class="bar" x="{bx}" y="{y}" width="{bar_w}" height="{height}" rx="1.5" style="{style}"/>'
        )
    return "\n    ".join(bars)


def render(track):
    """Build the SVG for a track dict (see latest_track), or an empty state when None."""
    now_playing = bool(track and track["now_playing"])
    if track:
        status = "NOW PLAYING" if now_playing else "RECENTLY PLAYED"
        title = clip(track["name"], 34)
        subtitle = clip(track["artist"] + (f" · {track['album']}" if track["album"] else ""), 44)
        art = art_data_uri(track["art_url"])
    else:
        status, title, subtitle, art = "RECENTLY PLAYED", "Nothing scrobbled yet", "Check back soon", None

    if art:
        art_svg = f'<image href="{art}" x="{PAD}" y="{PAD}" width="{ART}" height="{ART}" clip-path="url(#art)" preserveAspectRatio="xMidYMid slice"/>'
    else:
        # Simple note glyph on a muted tile when Last.fm has no artwork.
        cx, cy = PAD + ART / 2, PAD + ART / 2
        art_svg = (
            f'<rect x="{PAD}" y="{PAD}" width="{ART}" height="{ART}" rx="8" fill="{RULE}"/>'
            f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" font-size="40" fill="{MUTED}" font-family="{FONT}">♪</text>'
        )

    dot = (
        f'<circle class="dot" cx="{TEXT_X + 5}" cy="{PAD + 7}" r="4" fill="{ACCENT}"/>'
        if now_playing
        else f'<circle cx="{TEXT_X + 5}" cy="{PAD + 7}" r="4" fill="{MUTED}"/>'
    )
    eq_y = HEIGHT - PAD - 22
    bars_css = (
        f".bar{{fill:{ACCENT};transform-box:fill-box;transform-origin:bottom;"
        f"animation:eq 800ms ease-in-out infinite alternate}}"
        f"@keyframes eq{{from{{transform:scaleY(.15)}}to{{transform:scaleY(1)}}}}"
        f".dot{{animation:pulse 1.6s ease-in-out infinite}}"
        f"@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}"
        if now_playing
        else f".bar{{fill:{RULE};transform-box:fill-box;transform-origin:bottom;transform:scaleY(.25)}}"
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(status.title())}: {escape(title)} by {escape(subtitle)}">
  <title>{escape(status.title())}: {escape(title)} — {escape(subtitle)}</title>
  <style>
    text{{font-family:{FONT}}}
    {bars_css}
  </style>
  <defs>
    <clipPath id="art"><rect x="{PAD}" y="{PAD}" width="{ART}" height="{ART}" rx="8"/></clipPath>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="{BG}"/>
  {art_svg}
  {dot}
  <text x="{TEXT_X + 16}" y="{PAD + 11}" font-size="11" font-weight="600" letter-spacing="1.5" fill="{MUTED}">{escape(status)}</text>
  <text x="{TEXT_X}" y="{PAD + 38}" font-size="18" font-weight="700" fill="{FG}">{escape(title)}</text>
  <text x="{TEXT_X}" y="{PAD + 58}" font-size="13" fill="{MUTED}">{escape(subtitle)}</text>
  <g>
    {equalizer(now_playing, TEXT_X, eq_y, TEXT_W - 50)}
  </g>
  <text x="{WIDTH - PAD}" y="{HEIGHT - PAD - 4}" text-anchor="end" font-size="10" fill="{MUTED}" opacity="0.8">Last.fm</text>
</svg>
"""


SAMPLE = {
    "name": "Say Hello 2 Heaven - 25th Anniversary Mix",
    "artist": "Temple of the Dog",
    "album": "Temple of the Dog",
    "url": "https://www.last.fm/music/Temple+of+the+Dog/_/Say+Hello+2+Heaven",
    "now_playing": True,
    "art_url": "",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", default="ScottDataScienc", help="Last.fm username")
    ap.add_argument("--out", required=True, help="where to write the SVG")
    ap.add_argument("--sample", action="store_true", help="render built-in sample data instead of calling Last.fm")
    ap.add_argument("--idle", action="store_true", help="with --sample: render the 'recently played' state")
    args = ap.parse_args()

    if args.sample:
        track = dict(SAMPLE, now_playing=not args.idle)
    else:
        api_key = os.environ.get("LASTFM_API_KEY")
        if not api_key:
            sys.exit("LASTFM_API_KEY is not set")
        track = latest_track(args.user, api_key)
        print(f"latest track: {json.dumps(track)}")

    svg = render(track)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {args.out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
