from PIL import Image
import base64, io

IMG = r"C:\Users\Administrator\Desktop\1.jpg"
OUT = r"D:\military-civilian-quiz"
WHITE = (255, 255, 255, 255)

im = Image.open(IMG).convert("RGBA")
w, h = im.size
m = min(w, h)
sq = im.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))


def b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def icon(size, ratio):
    """纯白底 + 居中照片，照片边长 = size * ratio"""
    canvas = Image.new("RGBA", (size, size), WHITE)
    inner = sq.resize((round(size * ratio), round(size * ratio)), Image.Resampling.LANCZOS)
    off = (size - inner.size[0]) // 2
    canvas.paste(inner, (off, off), inner)
    return canvas


# 主图标：照片占 78%，白边只留在四角，被系统圆角裁掉也不伤照片
icon(192, 0.78).save(f"{OUT}\\icon-hamster-192.png")
icon(512, 0.78).save(f"{OUT}\\icon-hamster-512.png")
# maskable：安全区是中心直径 80% 的圆，照片收到 56% 才不被切
icon(512, 0.56).save(f"{OUT}\\icon-hamster-maskable.png")
# iOS 主屏图标：180x180 PNG，圆角由系统裁
icon(180, 0.78).save(f"{OUT}\\apple-touch-icon.png")

# 登录页内嵌用的 SVG（白底圆角，与 PWA 图标同款）
pwa = icon(192, 0.78)
svg = f'''<svg width="192" height="192" viewBox="0 0 192 192" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <rect width="192" height="192" rx="42" fill="#FFFFFF"/>
  <image xlink:href="data:image/png;base64,{b64(pwa)}" x="0" y="0" width="192" height="192" preserveAspectRatio="xMidYMid meet"/>
</svg>'''
open(f"{OUT}\\icon-hamster.svg", "w", encoding="utf-8").write(svg)

# 浏览器标签图标：原图直出，不加底色和边框
fav = sq.resize((192, 192), Image.Resampling.LANCZOS)
fsvg = f'''<svg width="192" height="192" viewBox="0 0 192 192" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image xlink:href="data:image/png;base64,{b64(fav)}" x="0" y="0" width="192" height="192" preserveAspectRatio="xMidYMid meet"/>
</svg>'''
open(f"{OUT}\\favicon.svg", "w", encoding="utf-8").write(fsvg)

print("done: 192/512/maskable/apple-touch PNG + icon-hamster.svg + favicon.svg")
