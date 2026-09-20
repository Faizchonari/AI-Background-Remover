"""Generate an icon for AI Background Remover using Pillow."""

from pathlib import Path
from PIL import Image, ImageDraw

def generate_icon():
    assets_dir = Path(__file__).resolve().parent
    assets_dir.mkdir(parents=True, exist_ok=True)
    ico_path = assets_dir / "app_icon.ico"
    png_path = assets_dir / "app_icon.png"

    # Create 256x256 icon
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background (vibrant blue/indigo gradient feel)
    # Background circle/rounded rect
    margin = 12
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=48,
        fill=(37, 99, 235, 255),  # Deep modern blue
        outline=(59, 130, 246, 255),
        width=4
    )

    # Draw a stylized cutout / silhouette symbol
    # Left half: filled subject silhouette (white)
    # Right half: checkerboard background showing background removal
    check_box = [margin + 16, margin + 16, size - margin - 16, size - margin - 16]
    
    # Draw central scissors / wand / portal graphic
    # Let's draw a person silhouette in white on left and transparency dots
    center_x = size // 2
    center_y = size // 2

    # Draw sparkling star / AI magic wand symbol
    # Sparkle 1 (center)
    def draw_star(cx, cy, r_outer, r_inner, fill):
        points = []
        for i in range(8):
            r = r_outer if i % 2 == 0 else r_inner
            import math
            angle = i * math.pi / 4
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(points, fill=fill)

    # Magic AI sparkles
    draw_star(center_x, center_y - 10, 56, 18, (255, 255, 255, 255))
    draw_star(center_x + 50, center_y + 40, 28, 9, (147, 197, 253, 255))
    draw_star(center_x - 45, center_y + 45, 22, 7, (224, 242, 254, 255))

    # Save PNG
    img.save(str(png_path), format="PNG")

    # Save ICO with standard sizes
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(str(ico_path), format="ICO", sizes=sizes)
    print(f"Generated icon: {ico_path}")

if __name__ == "__main__":
    generate_icon()
