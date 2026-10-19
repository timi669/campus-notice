# -*- coding: utf-8 -*-
"""生成微信小程序 TabBar 图标（4 个 tab × 普通/选中态 = 8 张 PNG）。
运行: python generate_icons.py
"""
from PIL import Image, ImageDraw

SIZE = 81          # 图标尺寸
NORMAL = "#8a8a8a" # 普通态颜色
ACTIVE = "#4F7DFB" # 选中态颜色（与 app.json selectedColor 一致）
W = 3              # 线条宽度


def new_canvas():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def draw_home(color):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # 屋顶：三角
    d.polygon([(40, 18), (16, 42), (64, 42)], outline=color, width=W)
    # 房身：矩形
    d.rectangle([(22, 40), (58, 66)], outline=color, width=W)
    # 门
    d.rectangle([(35, 52), (45, 66)], fill=color)
    return img


def draw_category(color):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    pad = 18
    s = 16
    gap = 6
    # 2x2 方格
    for i in range(2):
        for j in range(2):
            x0 = pad + i * (s + gap)
            y0 = pad + j * (s + gap)
            d.rectangle([x0, y0, x0 + s, y0 + s], outline=color, width=W)
    return img


def draw_search(color):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # 放大镜圆
    d.ellipse([(18, 16), (52, 50)], outline=color, width=W)
    # 镜柄
    d.line([(48, 46), (64, 62)], fill=color, width=W)
    # 柄端点加粗
    d.ellipse([(61, 59), (67, 65)], fill=color)
    return img


def draw_profile(color):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # 头
    d.ellipse([(29, 16), (51, 38)], outline=color, width=W)
    # 肩/身（半圆）
    d.arc([(14, 40), (66, 78)], 180, 360, fill=color, width=W)
    return img


ICONS = {
    "home": draw_home,
    "category": draw_category,
    "search": draw_search,
    "profile": draw_profile,
}

for name, fn in ICONS.items():
    fn(NORMAL).save(f"{name}.png")
    fn(ACTIVE).save(f"{name}-active.png")
    print(f"生成 {name}.png / {name}-active.png")

print("全部图标生成完毕。")
