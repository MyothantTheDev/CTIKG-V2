from PIL import Image
import numpy as np
import io

class ImageFilter:

  def calculate_entropy(self, img: Image):
    """Calculate Entropy of Image"""
    img = img.convert('L')
    histogram = img.histogram()
    histogram_length = sum(histogram)
    samples_probability = [float(h) / histogram_length for h in histogram]
    return -sum([p * np.log2(p) for p in samples_probability if p != 0])
  
  def is_stock_photo(self, img: Image) -> bool:
    thumb = img.resize((100, 100), Image.Resampling.BOX)
    quantized = thumb.quantize(colors=32)

    color_counts = quantized.histogram()
    color_counts = [c for c in color_counts if c > 0]

    if not color_counts: return True

    max_count = max(color_counts)
    total_pixels = 100 * 100
    dominance_ratio = max_count / total_pixels

    # print(f"Dominant Color Ratio: {dominance_ratio:.2f}")

    if dominance_ratio < 0.20:
      return True
    
    return False
  
  def is_useful_image(self,image_bytes: bytes = None):
    """
    Check if image is useful based on Size, Ratio, and Entropy
    """
    try:
      with Image.open(io.BytesIO(image_bytes)) as img_obj:
        file_size = len(image_bytes)
        width, height = img_obj.size

        if width < 300 or height < 200:
          return False
        
        if height == 0:
          return False
        
        if file_size < 5 * 1024:
          return False
        
        aspect_ratio = width / height
        if aspect_ratio > 4 or aspect_ratio < 0.2:
          return False
        
        if self.is_stock_photo(img_obj):
          return False
        
        entropy = self.calculate_entropy(img_obj)
        if entropy < 3.2:
          return False
      
        return True
    except Exception:
      return False