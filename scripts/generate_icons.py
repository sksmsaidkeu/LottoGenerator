"""PWA 아이콘 생성 스크립트 (site 브랜드 컬러 기반, 1회성 유틸리티)."""

from PIL import Image, ImageDraw, ImageFont

NAVY = (26, 41, 66)
GOLD = (169, 129, 47)
GOLD_LIGHT = (212, 175, 106)
WHITE = (255, 255, 255)


def make_icon(size, corner_ratio=0.22):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * corner_ratio)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=NAVY)

    ball_r = size * 0.32
    cx, cy = size / 2, size / 2
    draw.ellipse(
        [cx - ball_r, cy - ball_r, cx + ball_r, cy + ball_r],
        fill=GOLD,
        outline=GOLD_LIGHT,
        width=max(1, int(size * 0.01)),
    )

    text = "45"
    font_size = int(ball_r * 1.05)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), text, fill=NAVY, font=font)

    return img


if __name__ == "__main__":
    for size, name in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")]:
        icon = make_icon(size)
        if name == "apple-touch-icon.png":
            flat = Image.new("RGB", icon.size, NAVY)
            flat.paste(icon, mask=icon.split()[3])
            flat.save(f"icons/{name}")
        else:
            icon.save(f"icons/{name}")
        print(f"saved icons/{name}")
