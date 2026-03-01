import os
import fitz
import io
from .image_filter import ImageFilter, Image

class PDFProcessor:
  def __init__(self, image_output_dir: str = "extracted_images"):
    self.image_output_dir = image_output_dir
    self.image_filter = ImageFilter()

  def extract_content(self, rel_path: str = None):
    """
    Extracts both Text and Useful Images using PyMuPDF.
    """

    if not os.path.exists(rel_path):
      print(f"[*] PDF Not Found: {rel_path}")
      return None
    
    doc = fitz.open(rel_path)
    filename_base = os.path.splitext(os.path.basename(rel_path))[0]

    full_text = ""
    saved_images = []

    print(f"[*] Proessing: {filename_base}...")

    for i, page in enumerate(doc):

      text = page.get_text()
      if text:
        full_text += text + "\n"

      image_list = page.get_images(full=True)

      for img_idx, img in enumerate(image_list):
        try:
          xref = img[0]
          base_image = doc.extract_image(xref)
          img_bytes = base_image["image"]
          img_ext = base_image["ext"]

          # img_obj = Image.open(io.BytesIO(img_bytes))

          if self.image_filter.is_useful_image(image_bytes=img_bytes):
            img_filename = f"{filename_base}_p{i+1}_img{img_idx+1}.{img_ext}"
            save_path = os.path.join(self.image_output_dir, img_filename)

            with open(save_path, 'wb') as f:
              f.write(img_bytes)

            saved_images.append(save_path)

        except Exception as e:
          print(f"[*] Image Error on page {i+1}: {e}")

    doc.close()

    return {
      'text': full_text,
      'images': saved_images
    }