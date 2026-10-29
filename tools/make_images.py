"""Creates the launcher icon and the 16:9 Fire TV banner from the project's 512px icon."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

src, out_dir = sys.argv[1], sys.argv[2]
icon = Image.open(src).convert('RGBA')
icon.resize((256, 256), Image.LANCZOS).save(out_dir + '/icon.png', optimize=True)

W, H = 640, 360
bg = Image.new('RGBA', (W, H))
top, bottom = (10, 16, 32), (24, 34, 64)
d = ImageDraw.Draw(bg)
for y in range(H):
    t = y / (H - 1)
    d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse((-40, 40, 320, 360), fill=(10, 132, 255, 90))
bg = Image.alpha_composite(bg, glow.filter(ImageFilter.GaussianBlur(60)))
ic = icon.resize((176, 176), Image.LANCZOS)
bg.alpha_composite(ic, (52, (H - 176) // 2))
d = ImageDraw.Draw(bg)
f1 = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 58)
f2 = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Medium.otf', 24)
d.text((258, 118), 'Free My TV', font=f1, fill=(255, 255, 255, 255))
d.text((261, 196), 'Ad-free home screen', font=f2, fill=(170, 190, 220, 255))
bg.convert('RGB').save(out_dir + '/banner.png', optimize=True)
print('ok')
