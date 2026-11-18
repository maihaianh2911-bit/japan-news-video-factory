#!/usr/bin/env bash
# ffmpeg (with ffprobe) and the Noto CJK fonts of the frames (news/render.py reads
# /usr/share/fonts/opentype/noto/Noto{Sans,Serif}CJK-{Regular,Bold}.ttc) on a GitHub runner.
#
# The runners' package mirror is sometimes so slow that apt never finishes (18/11/2026: three tries of seven minutes
# each, none done, so no video). So apt gets one short try, and when it fails the same programs and fonts come from
# GitHub, which the runners reach quickly: a static ffmpeg build of BtbN/FFmpeg-Builds (GPL, with libx264 and aac)
# and the font files of notofonts/noto-cjk (the files the Ubuntu package fonts-noto-cjk holds).
#
# bash tools/install_deps.sh      (needs sudo and curl; exits 1 when neither way worked)
set -uo pipefail

FONTS=/usr/share/fonts/opentype/noto
FFMPEG_BUILD=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz
NOTO=https://github.com/notofonts/noto-cjk/raw/main
APT_TIMEOUTS=(-o Acquire::Retries=2 -o Acquire::http::Timeout=20)

fonts_ready() {
  local family weight file
  for family in Sans Serif; do
    for weight in Regular Bold; do
      file=$FONTS/Noto${family}CJK-$weight.ttc
      [[ -s $file && $(stat -c %s "$file") -gt 1000000 ]] || return 1
    done
  done
}

ready() {
  ffmpeg -hide_banner -version >/dev/null 2>&1 && ffprobe -hide_banner -version >/dev/null 2>&1 && fonts_ready
}

from_apt() {
  timeout 90 sudo apt-get update -qq "${APT_TIMEOUTS[@]}" \
    && timeout 240 sudo apt-get install -y -qq "${APT_TIMEOUTS[@]}" ffmpeg fonts-noto-cjk
}

from_github() {
  local tmp family weight
  tmp=$(mktemp -d)
  # /usr/local/bin comes before /usr/bin: this ffmpeg wins over one apt left half installed
  curl -fsSL --retry 3 --max-time 300 -o "$tmp/ffmpeg.tar.xz" "$FFMPEG_BUILD" \
    && tar -xJf "$tmp/ffmpeg.tar.xz" -C "$tmp" \
    && sudo install -m 755 "$tmp"/ffmpeg-*/bin/ffmpeg "$tmp"/ffmpeg-*/bin/ffprobe /usr/local/bin/ \
    || { echo "::warning::ffmpeg could not be downloaded from GitHub"; return 1; }
  hash -r
  sudo mkdir -p "$FONTS"
  for family in Sans Serif; do
    for weight in Regular Bold; do
      [[ -s $FONTS/Noto${family}CJK-$weight.ttc ]] && continue
      sudo curl -fsSL --retry 3 --max-time 300 -o "$FONTS/Noto${family}CJK-$weight.ttc" \
        "$NOTO/$family/OTC/Noto${family}CJK-$weight.ttc" \
        || { echo "::warning::Noto${family}CJK-$weight.ttc could not be downloaded from GitHub"; return 1; }
    done
  done
  sudo fc-cache -f >/dev/null 2>&1 || true
}

ready && exit 0
from_apt && ready && exit 0
echo "::warning::the package mirror is too slow or failing: ffmpeg and the Noto CJK fonts come from GitHub instead"
from_github && ready && { echo "ffmpeg and the Noto CJK fonts installed from GitHub"; exit 0; }
echo "::error::no ffmpeg, no ffprobe or no Noto CJK fonts: neither apt nor GitHub worked"
exit 1
