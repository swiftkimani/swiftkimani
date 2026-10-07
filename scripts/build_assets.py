#!/usr/bin/env python3
"""Builds the animated SVGs used by README.md into assets/.

GitHub strips scripts and styles from READMEs, so every effect here is CSS
animation inside a standalone SVG loaded through <img>. That context has no
web fonts, which is why the name is sampled into dots at build time instead
of being set as text.

Usage: python3 scripts/build_assets.py [--font path/to/condensed-bold.ttf]
Requires Pillow. Output is deterministic for a given font.
"""

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_FONT = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"

WIDTH = 880
INK, PANEL = "#07080c", "#0d1018"
FG, MUTED = "#e9eef7", "#8d97a8"
EMBER, ICE, OK = "#ffb35c", "#6aa8ff", "#5effc3"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
DISPLAY = "'Big Shoulders Display','DIN Condensed','Roboto Condensed','Arial Narrow',Impact,sans-serif"
EASE = "cubic-bezier(.2,.7,.1,1)"
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
RULE = f'stroke="{FG}" stroke-opacity=".12"'

NAME_FIRST, NAME_LAST = "SWIFT", "KIMANI"
TERMINAL_LINES = [
    ("whoami", "swift kimani · software engineer · nairobi, kenya"),
    ("ls ~/shipping", "kaziscout/ voice-mcp/ figma-canvas-mcp/ hyper-voice/ sauti-salama/"),
    ("cat stack.txt", "rust · typescript · go · python · next.js · react · tauri · postgres"),
    ("./status --now", "building voice and agent tooling that keeps working offline"),
]
HEADERS = {
    "work": ("01", "SELECTED WORK", "github.com/swiftkimani"),
    "shipped": ("02", "ALSO SHIPPED", "live demos linked"),
    "writing": ("03", "WRITING", "medium.com/@swiftkimani"),
    "signal": ("04", "SIGNAL", "commit telemetry"),
}
MARQUEE_ITEMS = ["RUST", "TYPESCRIPT", "GO", "MCP SERVERS", "VOICE", "AGENTS", "OFFLINE-FIRST", "NAIROBI"]
RING_PHRASE = "SWIFT KIMANI · NAIROBI · RUST · TYPESCRIPT · GO · "


def svg(height, body, style, label):
    """Wraps body in a full-width SVG document with an accessible label."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" role="img" aria-label="{label}">'
        f"<title>{label}</title><style>{style}{REDUCED}</style>{body}</svg>\n"
    )


def sample_dots(font_path, target_width, step):
    """Rasterises the name and returns (dots, height, split_x) on a regular grid."""
    font = ImageFont.truetype(font_path, 400)
    try:
        font.set_variation_by_axes([900])
    except OSError:
        pass  # static font: it has a single weight already
    text = f"{NAME_FIRST} {NAME_LAST}"
    left, top, right, bottom = font.getbbox(text)
    mask = Image.new("L", (right - left, bottom - top))
    ImageDraw.Draw(mask).text((-left, -top), text, fill=255, font=font)
    scale = mask.width / target_width
    height = mask.height / scale
    split_x = (font.getlength(NAME_FIRST) + font.getlength(" ") / 2 - left) / scale
    dots = []
    for col in range(int(target_width / step)):
        for row in range(int(height / step)):
            x, y = (col + 0.5) * step, (row + 0.5) * step
            if mask.getpixel((int(x * scale), int(y * scale))) > 127:
                dots.append((col, x, y))
    return dots, height, split_x


def hero_name(font_path, rng):
    """Dot-matrix name: dots fly in from eight directions, then a light sweep loops."""
    name_width, step, origin_x, origin_y = 780, 4.6, 50, 92
    dots, _, split_x = sample_dots(font_path, name_width, step)
    columns = {}
    for col, x, y in dots:
        columns.setdefault(col, []).append((x, y))
    parts = []
    for col, points in sorted(columns.items()):
        x = points[0][0]
        word = "wf" if x < split_x else "wl"
        sweep_delay = 2.6 + x / name_width * 1.3
        circles = "".join(
            f'<circle class="p s{rng.randrange(8)} e{min(11, int(px / name_width * 9) + rng.randrange(3))}" '
            f'cx="{origin_x + px:.1f}" cy="{origin_y + py:.1f}" r="1.6"/>'
            for px, py in points
        )
        parts.append(f'<g class="{word}" style="animation-delay:{sweep_delay:.2f}s">{circles}</g>')
    return "".join(parts)


def hero_style():
    """Keyframes for the hero: dot assembly, sweep, aurora drift, twinkle, pulse."""
    rules = [
        f".p{{animation:1.2s {EASE} both}}",
        f".wf{{fill:{FG};animation:sf 7s linear infinite}}",
        f".wl{{fill:{EMBER};animation:sl 7s linear infinite}}",
        f"@keyframes sf{{0%,9%,100%{{fill:{FG}}}4%{{fill:{EMBER}}}}}",
        f"@keyframes sl{{0%,9%,100%{{fill:{EMBER}}}4%{{fill:#fff}}}}",
        ".au{animation:au 16s ease-in-out infinite alternate}",
        ".au2{animation:au2 20s ease-in-out infinite alternate}",
        "@keyframes au{to{transform:translate(90px,24px)}}",
        "@keyframes au2{to{transform:translate(-110px,-18px)}}",
        ".tw{animation:tw 4s ease-in-out infinite}",
        "@keyframes tw{50%{opacity:.15}}",
        ".pu{animation:pu 1.8s ease-in-out infinite}",
        "@keyframes pu{50%{opacity:.25}}",
    ]
    for index in range(8):
        angle = index * math.pi / 4 + 0.3
        dx, dy = math.cos(angle) * 70, math.sin(angle) * 46
        rules.append(f".s{index}{{animation-name:i{index}}}")
        rules.append(f"@keyframes i{index}{{from{{transform:translate({dx:.0f}px,{dy:.0f}px);opacity:0}}}}")
    rules += [f".e{index}{{animation-delay:{0.15 + index * 0.13:.2f}s}}" for index in range(12)]
    return "".join(rules)


def hero_chrome(rng):
    """Static instrument frame: aurora, dust, labels, tagline and readout strip."""
    dust = "".join(
        f'<circle class="tw" style="animation-delay:-{rng.uniform(0, 4):.1f}s" cx="{rng.uniform(20, 860):.0f}" '
        f'cy="{rng.uniform(60, 300):.0f}" r="{rng.choice([0.6, 0.8, 1.1])}" fill="{FG}" opacity=".5"/>'
        for _ in range(70)
    )
    cells = [
        ("BASE", "Nairobi, Kenya · UTC+3"),
        ("BUILDS WITH", "Rust · TypeScript · Go"),
        ("FOCUS", "Voice · agents · offline-first"),
        ("STATUS", "Shipping in public"),
    ]
    readout = ""
    for index, (label, value) in enumerate(cells):
        x = 32 + index * 208
        value_x = x + 14 if label == "STATUS" else x
        readout += (
            f'<text x="{x}" y="338" font-family="{MONO}" font-size="10" letter-spacing="1.2" fill="{MUTED}">{label}</text>'
            f'<text x="{value_x}" y="360" font-family="{SANS}" font-size="14" font-weight="600" fill="{FG}">{value}</text>'
        )
        if index:
            readout += f'<line x1="{x - 16}" y1="316" x2="{x - 16}" y2="380" {RULE}/>'
    return (
        '<defs><filter id="b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="55"/></filter>'
        f'<clipPath id="c"><rect width="{WIDTH}" height="380" rx="16"/></clipPath></defs>'
        f'<g clip-path="url(#c)"><rect width="{WIDTH}" height="380" fill="{INK}"/>'
        f'<g filter="url(#b)" opacity=".5"><ellipse class="au" cx="210" cy="60" rx="230" ry="90" fill="#2a5bd7"/>'
        f'<ellipse class="au2" cx="700" cy="250" rx="210" ry="70" fill="{EMBER}" opacity=".45"/></g>{dust}'
        f'<text x="32" y="36" font-family="{MONO}" font-size="11" letter-spacing="1.4" fill="{MUTED}">'
        f'SWIFTKIMANI <tspan fill="{EMBER}">/</tspan> README.MD</text>'
        f'<text x="848" y="36" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="1.4" fill="{MUTED}">'
        "01°17′S 36°49′E</text>"
        f'<line x1="0" y1="54" x2="{WIDTH}" y2="54" {RULE}/><line x1="0" y1="316" x2="{WIDTH}" y2="316" {RULE}/>'
        f'<text x="32" y="268" font-family="{SANS}" font-size="16" fill="{FG}">Software engineer building voice interfaces, '
        f'agent tooling and <tspan fill="{EMBER}">software that works offline.</tspan></text>'
        f'<text x="32" y="294" font-family="{SANS}" font-size="14" fill="{MUTED}">'
        "Mostly Rust and TypeScript, with Go where throughput matters.</text>"
        f'{readout}<circle class="pu" cx="{32 + 3 * 208 + 4}" cy="355" r="4" fill="{OK}"/>'
    )


def build_hero(font_path):
    rng = random.Random(7)
    body = hero_chrome(rng) + hero_name(font_path, rng) + "</g>"
    label = "Swift Kimani. Software engineer in Nairobi building voice interfaces, agent tooling and offline-first software."
    return svg(380, body, hero_style(), label)


def terminal_timeline(lines):
    """Returns per-line (start, end, output) seconds and the loop length."""
    clock, schedule = 0.8, []
    for command, _ in lines:
        end = clock + len(command) * 0.075
        schedule.append((clock, end, end + 0.35))
        clock = end + 1.5
    return schedule, clock + 4.5


def terminal_line(index, line, timing, next_start, total):
    """One typed command and its output; returns (markup, css)."""
    (command, output), (start, end, shown) = line, timing
    char_width, x, y = 8.43, 52, 78 + index * 50
    width = len(command) * char_width + 4
    pct = lambda seconds: f"{seconds / total * 100:.2f}%"
    markup = (
        f'<text class="q{index}" x="32" y="{y}" fill="{EMBER}">›</text>'
        f'<text x="{x}" y="{y}" fill="{FG}" textLength="{len(command) * char_width:.1f}">{command}</text>'
        f'<g class="k{index}"><rect x="{x}" y="{y - 15}" width="{width + 12:.1f}" height="21" fill="{PANEL}"/>'
        f'<g class="c{index}"><rect class="bl" x="{x + 1}" y="{y - 13}" width="8" height="16" fill="{EMBER}"/></g></g>'
        f'<text class="o{index}" x="{x}" y="{y + 23}" fill="{MUTED}" textLength="{len(output) * char_width:.1f}">{output}</text>'
    )
    caret_off = f"{pct(next_start)}{{opacity:0}}" if next_start else ""
    css = (
        f".k{index}{{transform:translate({width:.1f}px);animation:k{index} {total:.2f}s steps({len(command)},end) infinite}}"
        f"@keyframes k{index}{{0%,{pct(start)}{{transform:translate(0)}}{pct(end)},100%{{transform:translate({width:.1f}px)}}}}"
        f".c{index}{{opacity:{0 if next_start else 1};animation:c{index} {total:.2f}s step-end infinite}}"
        f"@keyframes c{index}{{0%{{opacity:0}}{pct(start)}{{opacity:1}}{caret_off}100%{{opacity:{0 if next_start else 1}}}}}"
        f".q{index}{{animation:q{index} {total:.2f}s step-end infinite}}"
        f"@keyframes q{index}{{0%{{opacity:0}}{pct(start - 0.3)}{{opacity:1}}}}"
        f".o{index}{{animation:o{index} {total:.2f}s step-end infinite}}"
        f"@keyframes o{index}{{0%{{opacity:0}}{pct(shown)}{{opacity:1}}}}"
    )
    return markup, css


def build_terminal():
    schedule, total = terminal_timeline(TERMINAL_LINES)
    height = 78 + len(TERMINAL_LINES) * 50
    markup, css = "", f"text{{font-family:{MONO};font-size:14px}}.bl{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:0}}}}"
    for index, line in enumerate(TERMINAL_LINES):
        next_start = schedule[index + 1][0] if index + 1 < len(schedule) else None
        line_markup, line_css = terminal_line(index, line, schedule[index], next_start, total)
        markup, css = markup + line_markup, css + line_css
    lights = "".join(f'<circle cx="{34 + i * 18}" cy="24" r="5" fill="none" {RULE}/>' for i in range(3))
    body = (
        f'<rect width="{WIDTH}" height="{height}" rx="16" fill="{PANEL}"/>'
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1}" rx="15.5" fill="none" {RULE}/>'
        f'{lights}<text x="{WIDTH / 2}" y="28" text-anchor="middle" fill="{MUTED}" style="font-size:12px">swift@nairobi: ~</text>'
        f'<line x1="0" y1="46" x2="{WIDTH}" y2="46" {RULE}/>{markup}'
    )
    summary = "; ".join(f"{command}: {output}" for command, output in TERMINAL_LINES)
    return svg(height, body, css, f"Terminal session. {summary}")


def build_header(index_label, title, note, rng):
    """Section header whose title decodes from random glyphs, left to right."""
    cycle, char_width, x0, glyphs = 9, 13, 76, "#%&/<>=+*01"
    chars = ""
    for position, char in enumerate(title):
        if char == " ":
            continue
        x, settle = x0 + position * char_width, 0.4 + position * 0.055
        for frame in range(3):
            chars += (
                f'<text class="fl" style="animation-delay:{settle - (3 - frame) * 0.07:.2f}s" x="{x}" y="31" '
                f'fill="{EMBER}">{rng.choice(glyphs).replace("&", "&amp;").replace("<", "&lt;")}</text>'
            )
        chars += f'<text class="on" style="animation-delay:{settle:.2f}s" x="{x}" y="31" fill="{FG}">{char}</text>'
    style = (
        f"text{{font-family:{MONO};font-size:16px;font-weight:600;text-anchor:middle}}"
        f".fl{{opacity:0;animation:fl {cycle}s step-end infinite}}@keyframes fl{{0%{{opacity:1}}.8%,100%{{opacity:0}}}}"
        f".on{{animation:on {cycle}s step-end infinite backwards}}@keyframes on{{0%{{opacity:0}}.1%{{opacity:1}}96%,100%{{opacity:0}}}}"
        f".ln{{stroke-dasharray:{WIDTH};animation:ln {cycle}s {EASE} infinite}}@keyframes ln{{0%{{stroke-dashoffset:{WIDTH}}}18%,100%{{stroke-dashoffset:0}}}}"
    )
    body = (
        f'<rect width="{WIDTH}" height="52" rx="12" fill="{INK}"/>'
        f'<text x="38" y="31" fill="{EMBER}">{index_label}</text><text x="60" y="31" fill="{MUTED}">/</text>{chars}'
        f'<text x="848" y="30" fill="{MUTED}" style="font-size:11px;font-weight:400;text-anchor:end;letter-spacing:1.2px">{note.upper()}</text>'
        f'<line class="ln" x1="24" y1="43.5" x2="856" y2="43.5" stroke="{EMBER}" stroke-opacity=".5"/>'
    )
    return svg(52, body, style, f"{index_label} {title.title()}")


def build_marquee():
    """Looping band of outlined and solid display words with faded edges."""
    x, row = 0, ""
    for index, item in enumerate(MARQUEE_ITEMS):
        length = len(item) * 23
        paint = f'fill="{FG}"' if index % 3 == 2 else f'fill="none" stroke="{MUTED}" stroke-width="1"'
        row += f'<text x="{x}" y="58" textLength="{length}" lengthAdjust="spacingAndGlyphs" {paint}>{item}</text>'
        row += f'<circle cx="{x + length + 28}" cy="42" r="4" fill="{EMBER}"/>'
        x += length + 56
    style = (
        f"text{{font-family:{DISPLAY};font-size:46px;font-weight:800}}"
        f".m{{animation:m 32s linear infinite}}@keyframes m{{to{{transform:translate(-{x}px)}}}}"
    )
    body = (
        f'<defs><linearGradient id="f"><stop offset="0" stop-color="#000"/><stop offset=".1" stop-color="#fff"/>'
        f'<stop offset=".9" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
        f'<mask id="k"><rect width="{WIDTH}" height="84" fill="url(#f)"/></mask></defs>'
        f'<rect width="{WIDTH}" height="84" rx="12" fill="{INK}"/>'
        f'<g mask="url(#k)"><g class="m">{row}<g transform="translate({x})">{row}</g></g></g>'
    )
    return svg(84, body, style, "Rust, TypeScript, Go, MCP servers, voice, agents, offline-first, Nairobi")


def build_footer():
    """Concentric rings of type counter-rotating around a closing line."""
    height, cx, cy = 260, WIDTH / 2, 130
    defs, rings, style = "", "", f"text{{font-family:{MONO}}}"
    for index in range(12):
        radius = 96 + index * 32
        circumference = 2 * math.pi * radius
        repeats = max(1, round(circumference / (len(RING_PHRASE) * 8.6)))
        colour = EMBER if index % 4 == 1 else FG
        direction = "reverse" if index % 2 else "normal"
        defs += f'<path id="r{index}" d="M{cx - radius},{cy}a{radius},{radius} 0 1,1 {2 * radius},0a{radius},{radius} 0 1,1 -{2 * radius},0"/>'
        rings += (
            f'<text class="r" style="animation-duration:{50 + index * 9}s;animation-direction:{direction}" font-size="12" '
            f'fill="{colour}" opacity="{max(0.14, 0.6 - index * 0.04):.2f}"><textPath href="#r{index}" '
            f'textLength="{circumference:.0f}">{RING_PHRASE * repeats}</textPath></text>'
        )
    style += f".r{{transform-origin:{cx}px {cy}px;animation:r linear infinite}}@keyframes r{{to{{transform:rotate(360deg)}}}}"
    body = (
        f'<defs>{defs}<clipPath id="c"><rect width="{WIDTH}" height="{height}" rx="16"/></clipPath>'
        f'<radialGradient id="g"><stop offset=".55" stop-color="{INK}"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/></radialGradient></defs>'
        f'<g clip-path="url(#c)"><rect width="{WIDTH}" height="{height}" fill="{INK}"/>{rings}'
        f'<ellipse cx="{cx}" cy="{cy}" rx="250" ry="92" fill="url(#g)"/>'
        f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" fill="{FG}" style="font-family:{DISPLAY};font-size:52px;font-weight:800;letter-spacing:1px">'
        f'LET’S BUILD <tspan fill="{EMBER}">SOMETHING</tspan></text>'
        f'<text x="{cx}" y="{cy + 36}" text-anchor="middle" fill="{MUTED}" font-size="12" letter-spacing="1.4">BENARDKIMANI.CO.KE</text></g>'
    )
    return svg(height, body, style, "Let’s build something. benardkimani.co.ke")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--font", default=DEFAULT_FONT, help="condensed bold TTF sampled for the dot-matrix name")
    font_path = parser.parse_args().font
    rng = random.Random(11)
    outputs = {"hero.svg": build_hero(font_path), "terminal.svg": build_terminal(),
               "marquee.svg": build_marquee(), "footer.svg": build_footer()}
    for slug, (index_label, title, note) in HEADERS.items():
        outputs[f"header-{slug}.svg"] = build_header(index_label, title, note, rng)
    ASSETS.mkdir(exist_ok=True)
    for name, content in outputs.items():
        (ASSETS / name).write_text(content, encoding="utf-8")
        print(f"{name}: {len(content) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
