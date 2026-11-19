#!/usr/bin/env python3
"""Repackage the official OrbisFox homebrew browser as a Discord TV launcher.

This preserves the original OrbisFox EBOOT and Gecko resource payload except for
its UI/homepage artwork and browser-shell startup policy. It does not implement
Discord APIs or native voice/video.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ORIGINAL_SHA256 = "079417b7777a869fab48d37ac1d52eb09d44d50e3d1dda23a46f26b5d7c52834"
ORIGINAL_URL = (
    "https://github.com/Wkrotik/OrbisFox/releases/download/v0.69-alpha/"
    "OrbisFox-0.69-alpha-Homebrew.pkg"
)
TITLE_ID = "DCTV00001"
CONTENT_ID = "IV0000-DCTV00001_00-DISCORDTV0000001"
APP_VERSION = "0.1"
DISCORD_HOME = "https://discord.com/app"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(pkgtool: Path, *args: str, cwd: Path | None = None) -> None:
    command = ["dotnet", str(pkgtool), *map(str, args)]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def font(size: int, bold: bool = False):
    names = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    )
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def discord_mark(draw: ImageDraw.ImageDraw, box, fill=(255, 255, 255, 255)):
    """Draw a recognizable controller/bot silhouette without external assets."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    # Controller body and rounded shoulders
    points = [
        (x0 + .10*w, y0 + .34*h), (x0 + .23*w, y0 + .18*h),
        (x0 + .39*w, y0 + .11*h), (x0 + .47*w, y0 + .17*h),
        (x0 + .53*w, y0 + .17*h), (x0 + .61*w, y0 + .11*h),
        (x0 + .77*w, y0 + .18*h), (x0 + .90*w, y0 + .34*h),
        (x0 + .98*w, y0 + .78*h), (x0 + .89*w, y0 + .92*h),
        (x0 + .76*w, y0 + .89*h), (x0 + .64*w, y0 + .75*h),
        (x0 + .36*w, y0 + .75*h), (x0 + .24*w, y0 + .89*h),
        (x0 + .11*w, y0 + .92*h), (x0 + .02*w, y0 + .78*h),
    ]
    draw.polygon(points, fill=fill)
    draw.ellipse((x0 + .015*w, y0 + .63*h, x0 + .24*w, y0 + .98*h), fill=fill)
    draw.ellipse((x0 + .76*w, y0 + .63*h, x0 + .985*w, y0 + .98*h), fill=fill)
    blue = (88, 101, 242, 255)
    draw.rounded_rectangle((x0 + .20*w, y0 + .46*h, x0 + .41*w, y0 + .53*h),
                           radius=max(3, int(.03*w)), fill=blue)
    draw.rounded_rectangle((x0 + .27*w, y0 + .39*h, x0 + .34*w, y0 + .60*h),
                           radius=max(3, int(.03*w)), fill=blue)
    r = .055*w
    for cx in (x0 + .62*w, x0 + .79*w):
        cy = y0 + .50*h
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=blue)


def make_icon(path: Path) -> None:
    im = Image.new("RGBA", (512, 512), (88, 101, 242, 255))
    d = ImageDraw.Draw(im)
    # Soft inset highlight
    d.rounded_rectangle((20, 20, 492, 492), radius=112, outline=(255,255,255,28), width=4)
    discord_mark(d, (78, 104, 434, 408))
    im.save(path, format="PNG", optimize=True)


def make_splash(work: Path) -> None:
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (23, 24, 33, 255))
    px = im.load()
    # Smooth diagonal purple/blue gradient
    for y in range(h):
        for x in range(w):
            t = min(1.0, max(0.0, (x * .55 + y * .45) / (w * .7 + h * .3)))
            glow = max(0.0, 1.0 - (((x-1450)/1000)**2 + ((y-80)/800)**2)**.5)
            px[x, y] = (
                int(23 + 52*t + 12*glow),
                int(24 + 47*t + 15*glow),
                int(33 + 125*t + 45*glow), 255
            )
    # Add a restrained vignette.
    overlay = Image.new("RGBA", (w, h), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((48, 48, w-48, h-48), radius=70,
                         outline=(255,255,255,34), width=3)
    im = Image.alpha_composite(im, overlay)
    d = ImageDraw.Draw(im)
    discord_mark(d, (105, 285, 555, 665))
    d.text((650, 350), "Discord TV", font=font(118, True), fill=(255,255,255,255))
    d.text((660, 505), "DISCORD, EN TU TELEVISOR", font=font(38, True),
           fill=(220,224,255,235))
    d.rounded_rectangle((660, 610, 1170, 620), radius=5, fill=(255,255,255,110))
    d.text((660, 690), "Iniciando el navegador…", font=font(31),
           fill=(220,224,255,220))
    im.convert("RGB").save(work / "pic0.png", format="PNG", optimize=True)
    im.convert("RGB").save(work / "pic1.png", format="PNG", optimize=True)
    icon = work / "icon0.png"
    make_icon(icon)

    small = im.resize((1280, 720), Image.Resampling.LANCZOS).convert("RGBA")
    header = struct.pack("<8sII", b"ORBFIMG1", 1280, 720)
    (work / "splash.rgba").write_bytes(header + small.tobytes())


def patch_omni(omni: Path) -> dict:
    if not omni.is_file():
        raise RuntimeError("Original package is missing gecko/omni.ja")
    temporary = omni.with_suffix(".ja.discord-tv.tmp")
    required = {
        "chrome/orbisfox/content/browser-shell-model.js",
        "chrome/orbisfox/content/browser-shell-host.js",
        "chrome/orbisfox/content/browser-shell-ui.js",
        "chrome/orbisfox/content/browser.xhtml",
        "chrome/orbisfox/content/browser.css",
    }
    changed = {}
    with zipfile.ZipFile(omni, "r") as source:
        names = set(source.namelist())
        missing = required - names
        if missing:
            raise RuntimeError("OrbisFox resource archive is missing: " + ", ".join(sorted(missing)))
        with zipfile.ZipFile(temporary, "w") as target:
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename in required or info.filename == "chrome/orbisfox/content/browser.xhtml":
                    text = data.decode("utf-8")
                    original = text
                    if info.filename.endswith("browser-shell-model.js"):
                        needle = 'homePage:""'
                        if needle not in text:
                            raise RuntimeError("Could not find default home page setting in Gecko shell model")
                        text = text.replace(needle, f'homePage:"{DISCORD_HOME}"', 1)
                    elif info.filename.endswith("browser-shell-host.js"):
                        text = text.replace(
                            'const homeTarget=()=>{const page=settings.snapshot().homePage;return page&&gates().web?page:"home";};',
                            f'const homeTarget=()=>"{DISCORD_HOME}";',
                            1
                        )
                        start_marker = "    const urls=pendingSession||[];pendingSession=null;"
                        start = text.find(start_marker)
                        if start < 0:
                            raise RuntimeError("Could not locate the browser startup/session restore block")
                        end = text.find("\n  };", start)
                        if end < 0:
                            raise RuntimeError("Could not find end of browser startup function")
                        old_block = text[start:end]
                        if "else if(untouched&&settings.snapshot().homePage)" not in old_block:
                            raise RuntimeError("Unexpected browser startup policy; refusing a blind patch")
                        new_block = (
                            "    pendingSession=null;\n"
                            f'    if(untouched)load("{DISCORD_HOME}",first);'
                        )
                        text = text[:start] + new_block + text[end:]
                    elif info.filename.endswith("browser.xhtml"):
                        text = text.replace("<title>OrbisFox</title>", "<title>Discord TV</title>")
                        text = text.replace('<span id="brand">OrbisFox</span>',
                                            '<span id="brand">Discord TV</span>')
                        text = text.replace('<h1>OrbisFox</h1>', '<h1>Discord TV</h1>')
                        text = text.replace('aria-label="OrbisFox home"', 'aria-label="Discord TV home"')
                    elif info.filename.endswith("browser.css"):
                        text += (
                            "\n/* Discord TV kiosk presentation */\n"
                            "#browser-header,#browser-footer{display:none!important;}\n"
                            "#menu-panel{top:16px!important;right:16px!important;}\n"
                            "#settings-panel{top:12px!important;}\n"
                            "#fullscreen-notice{top:12px!important;}\n"
                        )
                    elif info.filename.endswith("browser-shell-ui.js"):
                        text = text.replace("OrbisFox Home", "Discord TV")
                    data = text.encode("utf-8")
                    if data != original.encode("utf-8"):
                        changed[info.filename] = {
                            "before": hashlib.sha256(original.encode("utf-8")).hexdigest(),
                            "after": hashlib.sha256(data).hexdigest()
                        }
                target.writestr(info, data)
    if not changed:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("No Discord TV resource modifications were applied")
    temporary.replace(omni)
    return changed


def write_offline_page(path: Path) -> None:
    html = """<!doctype html>
<html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Discord TV</title>
<style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;font-family:Arial,sans-serif}
body{display:grid;place-items:center;color:#fff;background:radial-gradient(ellipse at 75% 15%,#414dc1,#171821 65%)}
main{text-align:center;padding:44px;max-width:900px}
h1{font-size:64px;margin:18px 0}p{font-size:24px;line-height:1.5;color:#d9dcf7}
small{font-size:17px;color:#aeb4d9}
</style>
<main><h1>Discord TV</h1>
<p>El navegador está preparando la conexión segura con Discord.</p>
<small>Cuando termine la comprobación de red, Discord se abrirá automáticamente.</small>
</main></html>
"""
    path.write_text(html, encoding="utf-8")


def set_sfo(pkgtool: Path, sfo: Path, name: str, value: str, maxsize: int) -> None:
    run(pkgtool, "sfo_setentry", "--value", value, "--type", "utf8",
        "--maxsize", str(maxsize), str(sfo), name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pkgtool", required=True, type=Path)
    parser.add_argument("--source-pkg", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    pkgtool = args.pkgtool.resolve()
    source_pkg = args.source_pkg.resolve()
    output = args.output_dir.resolve()
    if not pkgtool.is_file() or not source_pkg.is_file():
        raise SystemExit("Missing PkgTool.Core.dll or original OrbisFox PKG")
    if len(TITLE_ID) != 9 or len(CONTENT_ID) >= 48:
        raise SystemExit("Invalid PS4 package identity")
    if digest(source_pkg) != ORIGINAL_SHA256:
        raise SystemExit("Original OrbisFox PKG SHA-256 does not match the pinned release")

    output.mkdir(parents=True, exist_ok=True)
    work = output / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()

    print("1/7 Validating the pinned original package", flush=True)
    run(pkgtool, "pkg_validate", str(source_pkg))

    print("2/7 Extracting the original package and creating its GP4 project", flush=True)
    project_dir = work / "project"
    project_dir.mkdir()
    run(pkgtool, "pkg_makegp4", str(source_pkg), str(project_dir))
    gp4 = project_dir / "Project.gp4"
    if not gp4.is_file():
        raise RuntimeError("PkgTool did not produce Project.gp4")
    pfs = project_dir / "gecko" / "omni.ja"
    sfo = project_dir / "sce_sys" / "param.sfo"
    if not sfo.is_file():
        raise RuntimeError("Extracted package does not contain sce_sys/param.sfo")

    print("3/7 Rebranding Gecko startup, kiosk chrome and icon artwork", flush=True)
    changed = patch_omni(pfs)
    write_offline_page(project_dir / "assets" / "offline.html")
    artwork = work / "artwork"
    artwork.mkdir()
    make_splash(artwork)
    system = project_dir / "sce_sys"
    shutil.copy2(artwork / "icon0.png", system / "icon0.png")
    shutil.copy2(artwork / "pic0.png", system / "pic0.png")
    shutil.copy2(artwork / "pic1.png", system / "pic1.png")
    shutil.copy2(artwork / "splash.rgba", project_dir / "assets" / "splash.rgba")

    print("4/7 Setting standalone PS4 package identity", flush=True)
    set_sfo(pkgtool, sfo, "TITLE", "Discord TV", 128)
    set_sfo(pkgtool, sfo, "TITLE_ID", TITLE_ID, 12)
    set_sfo(pkgtool, sfo, "CONTENT_ID", CONTENT_ID, 48)
    set_sfo(pkgtool, sfo, "APP_VER", APP_VERSION, 8)
    set_sfo(pkgtool, sfo, "VERSION", APP_VERSION, 8)

    tree = ET.parse(gp4)
    package = tree.getroot().find("./volume/package")
    if package is None:
        raise RuntimeError("Project.gp4 does not contain volume/package metadata")
    package.set("content_id", CONTENT_ID)
    ET.indent(tree, space="  ")
    tree.write(gp4, encoding="utf-8", xml_declaration=True)

    print("5/7 Building the new fake PKG", flush=True)
    package_out = work / "built"
    package_out.mkdir()
    run(pkgtool, "pkg_build", str(gp4), str(package_out))
    built = package_out / (CONTENT_ID + ".pkg")
    if not built.is_file():
        choices = list(package_out.glob("*.pkg"))
        if len(choices) != 1:
            raise RuntimeError("PkgTool did not emit exactly one PKG")
        built = choices[0]

    print("6/7 Validating the Discord TV PKG and its SFO identity", flush=True)
    run(pkgtool, "pkg_validate", str(built))
    run(pkgtool, "sfo_listentries", str(sfo))
    final_pkg = output / "Discord-TV-PS4.pkg"
    shutil.copy2(built, final_pkg)
    final_sha = digest(final_pkg)

    print("7/7 Writing provenance and limitations report", flush=True)
    report = {
        "product": "Discord TV",
        "version": APP_VERSION,
        "package": final_pkg.name,
        "title_id": TITLE_ID,
        "content_id": CONTENT_ID,
        "source_browser": "OrbisFox 0.69 alpha Homebrew package",
        "source_url": ORIGINAL_URL,
        "source_pkg_sha256": ORIGINAL_SHA256,
        "package_sha256": final_sha,
        "package_bytes": final_pkg.stat().st_size,
        "changed_gecko_resources": changed,
        "discord_homepage": DISCORD_HOME,
        "fullscreen_kiosk": True,
        "dualshock_mapping": "Original OrbisFox mapping is retained",
        "login": "Official Discord website; no credentials or tokens are collected by this package",
        "profile_note": "The EBOOT retains OrbisFox's /data/orbisfox/homebrew-profile path; data is shared with the matching OrbisFox SDK build.",
        "known_limits": [
            "This is a rebranded OrbisFox Gecko browser launcher, not an official Discord client.",
            "Discord Web may load partially or fail because OrbisFox remains experimental.",
            "Voice/video calls, screen share, notifications and DAVE end-to-end voice are not certified and may not work.",
            "No new console test was performed by this build workflow.",
            "OrbisFox content is not process-sandboxed; avoid sensitive account use until tested."
        ]
    }
    (output / "BUILD-REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "BUILD-REPORT.txt").write_text(
        "Discord TV PS4 — build report\n"
        f"Version: {APP_VERSION}\nTitle ID: {TITLE_ID}\nContent ID: {CONTENT_ID}\n"
        f"PKG bytes: {final_pkg.stat().st_size}\nSHA-256: {final_sha}\n"
        "Base: OrbisFox 0.69 alpha Homebrew\n"
        "Startup: https://discord.com/app after the browser's network/TLS gates\n"
        "Display: browser chrome hidden; Options menu retained\n"
        "Controller: original OrbisFox DualShock mapping retained\n"
        "Limitations: not an official Discord client; browser compatibility and voice/video are unverified;\n"
        "no PS4 console launch test was performed; profile path is shared with OrbisFox SDK.\n",
        encoding="utf-8"
    )
    (output / "SHA256SUMS.txt").write_text(
        f"{final_sha}  {final_pkg.name}\n", encoding="ascii"
    )
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
