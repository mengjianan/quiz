from PIL import Image
import base64, io

IMG = r"C:\Users\Administrator\Desktop\1.jpg"
im = Image.open(IMG).convert("RGBA")

# 裁剪为正方形（取中心），之后从同一张正方形图派生出两种图标
w, h = im.size
m = min(w, h)
sq = im.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))

def b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# 1) PWA 图标：纯白圆角底 + 内图放大到 140（原 100）
inner = sq.resize((140, 140), Image.Resampling.LANCZOS)
pwa = Image.new("RGBA", (192, 192), (255, 255, 255, 255))
pwa.paste(inner, (26, 26), inner)
svg = f'''<svg width="192" height="192" viewBox="0 0 192 192" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <rect width="192" height="192" rx="42" fill="#FFFFFF"/>
  <image xlink:href="data:image/png;base64,{b64(pwa)}" x="0" y="0" width="192" height="192" preserveAspectRatio="xMidYMid meet"/>
</svg>'''
open(r"D:\military-civilian-quiz\icon-hamster.svg", "w", encoding="utf-8").write(svg)

# 2) 浏览器标签图标：直接用原图，不加底色和边框
fav = sq.resize((192, 192), Image.Resampling.LANCZOS)
fsvg = f'''<svg width="192" height="192" viewBox="0 0 192 192" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image xlink:href="data:image/png;base64,{b64(fav)}" x="0" y="0" width="192" height="192" preserveAspectRatio="xMidYMid meet"/>
</svg>'''
open(r"D:\military-civilian-quiz\favicon.svg", "w", encoding="utf-8").write(fsvg)

print("icon-hamster.svg (white bg, bigger) + favicon.svg (original photo) done")