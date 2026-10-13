"""Rasterize the code-native Solem S mark for 16px browser tabs."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
icon = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(icon)
draw.rounded_rectangle((0, 0, 255, 255), radius=54, fill="#38BDF8")
# Bold angular S; a solid bright tile remains visible on dark AND light tabs.
draw.polygon([(64,52),(199,52),(173,89),(104,89),(84,112),(180,112),
              (199,142),(148,204),(48,204),(73,167),(130,167),(149,145),
              (60,145),(40,115)], fill="#08192C")
icon.resize((64,64), Image.Resampling.LANCZOS).save(root / "assets/solem-icon.png")
icon.save(root / "assets/solem-icon-large.png")
