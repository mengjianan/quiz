from PIL import Image, ImageOps
import base64
import io

# 打开原图
img_path = r"C:\Users\Administrator\Desktop\1.jpg"
im = Image.open(img_path).convert("RGBA")

# 裁剪为正方形（取中心）
w, h = im.size
min_dim = min(w, h)
left = (w - min_dim) // 2
top = (h - min_dim) // 2
im = im.crop((left, top, left + min_dim, top + min_dim))

# 缩放到 100x100（在 192x192 画布中居中）
im = im.resize((100, 100), Image.Resampling.LANCZOS)

# 创建 192x192 的暖色背景画布 (#FCEBD5)
canvas = Image.new("RGBA", (192, 192), (252, 235, 213, 255))

# 先画一个白色的圆形/圆角底座作为白色边框底衬（例如在中心放置一个 126x126 的白色圆角矩形或圆）
# 这里我们用画图或者直接贴一个带白边的图
# 让我们用纯 Pillow 画一个带白边的圆形容器：
# 画布尺寸 192x192，中心 (96,96)，半径 66 的白色圆盘（即白色边框 + 留白）
from PIL import ImageDraw
draw = ImageDraw.Draw(canvas)
# 绘制白色圆形底盘（直径 140，半径 70，中心 96,96）
draw.ellipse([96 - 72, 96 - 72, 96 + 72, 96 + 72], fill=(255, 255, 255, 255))

# 把原图粘贴在白色底盘中心 (96 - 50 = 46)
canvas.paste(im, (46, 46), im)

# 保存为 PNG 字节流转 base64
buffered = io.BytesIO()
canvas.save(buffered, format="PNG")
img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

# 生成新的 SVG（暖色背景 + 带有白色圆形内衬及头像）
svg_content = f'''<svg width="192" height="192" viewBox="0 0 192 192" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <rect width="192" height="192" rx="42" fill="#FCEBD5"/>
  <circle cx="96" cy="96" r="72" fill="#FFFFFF"/>
  <image xlink:href="data:image/png;base64,{img_str}" x="0" y="0" width="192" height="192" preserveAspectRatio="xMidYMid meet"/>
</svg>'''

with open("D:\\military-civilian-quiz\\icon-hamster.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

print("Icon updated successfully with white border!")
