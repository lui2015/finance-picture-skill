#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三张图讲清一个金融概念 —— 文字为主的知识卡排版引擎。

用法:
    python3 make_cards.py /abs/path/config.json
    python3 make_cards.py                       # 默认读当前目录 config.json

输入: 3 张无文字竖版插画（约 1024x1536）+ config.json
输出: 3 张 1080x1440 PNG + 1 张三联预览图

所有中文由系统字体绘制，绝不交给图像模型生成，避免乱码。
版式：上方 60% 结构化文字 / 下方 30% 左图右卡配图区 / 底部 5% 金句条。
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1080, 1440

# (字体路径, 常规 index, 粗体 index)。macOS 常见环境里 PingFang.ttc 常不存在。
FONT_SPECS = [
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0, 2),  # W3 / W6
    ("/System/Library/Fonts/PingFang.ttc", 0, 1),
    ("/System/Library/Fonts/STHeiti Light.ttc", 1, 1),
    ("/Library/Fonts/Arial Unicode.ttf", 0, 0),
]
FONT_PATH, REG_IDX, BOLD_IDX = FONT_SPECS[0]
for _p, _r, _b in FONT_SPECS:
    if os.path.exists(_p):
        FONT_PATH, REG_IDX, BOLD_IDX = _p, _r, _b
        break
BOLD_STROKE = 0 if "Hiragino Sans GB" in FONT_PATH else 1

BG = (250, 246, 237)
CARD = (255, 255, 255)
CARD_LINE = (232, 224, 208)
NAVY = (20, 56, 96)
SLATE = (76, 99, 122)
GOLD = (168, 116, 22)
RED = (183, 61, 44)
GOLD_LIGHT = (247, 216, 145)
COLORS = {"navy": NAVY, "gold": GOLD, "red": RED, "slate": SLATE}


def font(size, bold=False):
    return ImageFont.truetype(FONT_PATH, size, index=BOLD_IDX if bold else REG_IDX)


def text_w(d, s, f):
    b = d.textbbox((0, 0), s, font=f, anchor="lt")
    return b[2] - b[0]


def fit_font(d, s, size, bold, max_w):
    """自动缩字号，保证单行放得下。"""
    f = font(size, bold)
    while text_w(d, s, f) > max_w and size > 24:
        size -= 1
        f = font(size, bold)
    return f


def wrap_text(d, s, f, max_w):
    lines, cur = [], ""
    for ch in s:
        if cur and text_w(d, cur + ch, f) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def fit_lines(d, s, size, bold, max_w, max_lines=2):
    """自动缩字号 + 折行，避免最后一行只剩一两个孤字。"""
    lines = []
    while size > 22:
        f = font(size, bold)
        lines = wrap_text(d, s, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 1
    return f, lines[:max_lines]


def clean_patch(src, box):
    """抹掉插画里压住小字的干扰元素（金币等），用上下天空色渐变 + 羽化补回。"""
    im = src.copy()
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) // 2
    c_top = src.getpixel((cx, max(0, y0 - 24)))
    c_bot = src.getpixel((cx, min(src.height - 1, y1 + 26)))
    patch = Image.new("RGB", (w, h))
    pd = ImageDraw.Draw(patch)
    for j in range(h):
        t = j / max(1, h - 1)
        c = tuple(int(c_top[k] * (1 - t) + c_bot[k] * t) for k in range(3))
        pd.line((0, j, w, j), fill=c)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((8, 8, w - 8, h - 8), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(22))
    im.paste(patch, (x0, y0), mask)
    return im


def build(base, cfg, card, idx):
    src = Image.open(os.path.join(base, cfg["scenes"][idx])).convert("RGB")
    patches = cfg.get("clean_patches") or [None, None, None]
    if patches[idx]:
        src = clean_patch(src, patches[idx])

    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)

    # 顶部：系列标签 + 页码
    f_label = font(28, True)
    lw = text_w(d, card["label"], f_label) + 58
    d.rounded_rectangle((72, 56, 72 + lw, 112), radius=28, fill=NAVY)
    d.text((101, 84), card["label"], font=f_label, fill=(255, 252, 245), anchor="lm")
    d.text((1008, 84), card["page"], font=font(30, True), fill=NAVY, anchor="ra")

    # 主标题（分段着色）
    cx = 72
    for seg, cname in card["title"]:
        f = font(78, True)
        col = COLORS.get(cname, NAVY)
        d.text((cx, 148), seg, font=f, fill=col, anchor="la",
               stroke_width=BOLD_STROKE, stroke_fill=col)
        cx += text_w(d, seg, f)

    # 导语
    f_lead = fit_font(d, card["lead"], 38, False, W - 144)
    d.text((72, 262), card["lead"], font=f_lead, fill=SLATE, anchor="la")

    # 金色短线
    d.rounded_rectangle((72, 328, 164, 336), radius=4, fill=GOLD)

    # 三条要点卡片
    for j, (head, desc) in enumerate(card["points"]):
        by = 365 + j * 167
        d.rounded_rectangle((60, by, 1020, by + 150), radius=22,
                            fill=CARD, outline=CARD_LINE, width=2)
        d.ellipse((94, by + 47, 150, by + 103), fill=NAVY if j != 2 else GOLD)
        d.text((122, by + 75), str(j + 1), font=font(30, True),
               fill=(255, 255, 255), anchor="mm")
        f_head = font(40, True)
        d.text((178, by + 28), head, font=f_head, fill=NAVY, anchor="la",
               stroke_width=BOLD_STROKE, stroke_fill=NAVY)
        f_desc = fit_font(d, desc, 32, False, 1020 - 178 - 28)
        d.text((178, by + 92), desc, font=f_desc, fill=SLATE, anchor="la")

    # 配图区：柔化场景底 + 左侧完整角色竖像 + 右侧信息卡
    px, py, pw, ph = 72, 870, 936, 465
    tile = ImageOps.fit(src, (pw, ph), method=Image.LANCZOS, centering=(0.5, 0.42))
    tile = tile.filter(ImageFilter.GaussianBlur(20))
    tile = Image.blend(tile, Image.new("RGB", (pw, ph), (255, 252, 245)), 0.30)

    pic_w, pic_h = 370, ph - 24
    pic = ImageOps.fit(src.crop(tuple(cfg["portraits"][idx])), (pic_w, pic_h),
                       method=Image.LANCZOS, centering=(0.5, 0.45))
    bx, by = 24, 12
    td = ImageDraw.Draw(tile)
    td.rounded_rectangle((bx - 5, by - 5, bx + pic_w + 5, by + pic_h + 5),
                         radius=26, fill=(255, 255, 255))
    pmask = Image.new("L", (pic_w, pic_h), 0)
    ImageDraw.Draw(pmask).rounded_rectangle((0, 0, pic_w - 1, pic_h - 1),
                                            radius=22, fill=255)
    tile.paste(pic, (bx, by), pmask)

    cd = ImageDraw.Draw(tile)
    cx0, cy0, cx1, cy1 = 414, 40, 912, 425
    cd.rounded_rectangle((cx0, cy0, cx1, cy1), radius=22,
                         fill=(255, 255, 255), outline=(232, 222, 202), width=2)
    ix = cx0 + 30
    avail = cx1 - ix - 28
    aside = card["aside"]

    f_tag = font(25, True)
    tag_w = text_w(cd, aside["tag"], f_tag) + 44
    cd.rounded_rectangle((ix, cy0 + 28, ix + tag_w, cy0 + 74), radius=23, fill=GOLD)
    cd.text((ix + 22, cy0 + 51), aside["tag"], font=f_tag,
            fill=(255, 255, 255), anchor="lm")

    yb = cy0 + 108
    for line in aside["big"]:
        f_big = font(40, True)
        cd.text((ix, yb), line, font=f_big, fill=NAVY, anchor="la",
                stroke_width=BOLD_STROKE, stroke_fill=NAVY)
        yb += 56

    cd.line((ix, cy0 + 240, cx1 - 30, cy0 + 240), fill=(228, 216, 192), width=2)
    f_small, lines = fit_lines(cd, aside["small"], 27, False, avail, 2)
    ys = cy0 + 262
    for line in lines:
        cd.text((ix, ys), line, font=f_small, fill=SLATE, anchor="la")
        ys += 38

    outer = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(outer).rounded_rectangle((0, 0, pw - 1, ph - 1),
                                            radius=28, fill=255)
    canvas.paste(tile, (px, py), outer)
    d.rounded_rectangle((px, py, px + pw, py + ph), radius=28,
                        outline=(222, 206, 176), width=3)

    # 底部金句条
    d.rounded_rectangle((72, 1355, 1008, 1420), radius=30, fill=NAVY)
    f_punch = fit_font(d, card["punch"], 36, True, 880)
    d.text((100, 1387), card["punch"], font=f_punch, fill=GOLD_LIGHT, anchor="lm",
           stroke_width=BOLD_STROKE, stroke_fill=GOLD_LIGHT)

    out = os.path.join(base, card["out"])
    canvas.save(out, "PNG")
    print("saved", out)
    return out


def contact_sheet(base, paths, name):
    tw, th = 320, 427
    gap, pad = 24, 32
    sheet = Image.new("RGB", (tw * 3 + gap * 2 + pad * 2, th + pad * 2), (240, 235, 224))
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
        x = pad + i * (tw + gap)
        ImageDraw.Draw(sheet).rounded_rectangle(
            (x - 3, pad - 3, x + tw + 3, pad + th + 3),
            radius=10, fill=(214, 202, 178))
        sheet.paste(im, (x, pad))
    out = os.path.join(base, name)
    sheet.save(out, "PNG")
    print("saved", out)


def main():
    cfg_path = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "config.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    base = cfg.get("base_dir", ".")
    if not os.path.isabs(base):
        base = os.path.join(os.path.dirname(cfg_path), base)
    if len(cfg["scenes"]) != 3 or len(cfg["cards"]) != 3:
        raise SystemExit("需要正好 3 个 scenes 和 3 个 cards")
    print("font:", FONT_PATH)
    outs = [build(base, cfg, c, i) for i, c in enumerate(cfg["cards"])]
    contact_sheet(base, outs, cfg.get("preview", "preview.png"))


if __name__ == "__main__":
    main()
