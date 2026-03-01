import os
import json
import hashlib
import mimetypes
from core.image_filter import ImageFilter
from urllib.parse import urlparse

class Pipeline:
  def __init__(self, output_dir, downloader):
    self.output_dir = output_dir
    self.images_dir = os.path.join(output_dir, "images")
    self.data_file = os.path.join(output_dir, "articles.jsonl")
    self.downloader = downloader # Re-use the downloader session
    self.imageFilter = ImageFilter()
    
    os.makedirs(self.images_dir, exist_ok=True)

  def get_extension(self, url, content_type):
    parsed_path = urlparse(url).path
    ext = os.path.splitext(parsed_path)[1].lower()
    
    if not ext or len(ext) > 5:
      ext = mimetypes.guess_extension(content_type)
    
    return ext if ext else ".jpg"

  def process_images(self, image_urls):
    saved_paths = []
    
    for url in image_urls:
      try:
        parsed_path = urlparse(url).path
        temp_ext = os.path.splitext(parsed_path)[1].lower() or ".jpg"
        if len(temp_ext) > 5: temp_ext = ".jpg"

        file_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{file_hash}{temp_ext}"
        save_path = os.path.join(self.images_dir, filename)

        if os.path.exists(save_path):
          print(f"   [.] Skipping existing image: {filename}")
          saved_paths.append(save_path)
          continue

        resp = self.downloader.fetch(url)
        if not resp: 
          print(f"   [-] Download Failed (Network/403): {url}")
          continue

        if resp.status_code != 200:
          print(f"   [-] HTTP Error {resp.status_code}: {url}")
          continue
        
        ct = resp.headers.get('Content-Type', '').lower()
        if 'image' not in ct or 'svg' in ct: 
          print(f"   [-] Invalid Content-Type ({ct}): {url}")
          continue

        final_ext = self.get_extension(url, ct)
        final_filename = f"{file_hash}{final_ext}"
        final_save_path = os.path.join(self.images_dir, final_filename)

        if self.imageFilter.is_useful_image(resp.content):
          with open(final_save_path, "wb") as f:
            f.write(resp.content)
          
          saved_paths.append(final_filename)
          print(f"   [+] Image Saved: {final_filename}")
      
      except Exception as e:
        print(f"   [!] Error processing image {url}: {e}")

    return saved_paths

  def save_article(self, data):
    with open(self.data_file, 'a', encoding='utf-8') as f:
      f.write(json.dumps(data) + "\n")