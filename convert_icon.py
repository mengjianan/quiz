from PIL import Image
import svglib.svglib
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

def svg_to_png(svg_path, png_path, size=(192, 192)):
    """将SVG转换为PNG"""
    drawing = svg2rlg(svg_path)
    renderPM.drawToFile(drawing, png_path, fmt='PNG', dpi=300)
    print(f"已将 {svg_path} 转换为 {png_path}")

# 创建不同尺寸的图标
svg_path = "icon-hamster.svg"

# 192x192 图标
svg_to_png(svg_path, "icon-192.png", (192, 192))

# 512x512 图标
svg_to_png(svg_path, "icon-512.png", (512, 512))

print("图标转换完成！")