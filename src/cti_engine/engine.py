# core/engine.py
import concurrent.futures
import json
import os
from .downloader import Downloader
from .parser import PageParser
from .pipeline import Pipeline

class CTI_Engine:
  def __init__(self, config_path, output_dir):
    self.output_dir = output_dir  # Dynamic Path
    
    if not os.path.exists(self.output_dir):
      os.makedirs(self.output_dir)
      print(f"[*] Created output directory: {self.output_dir}")

    self.downloader = Downloader()
    
    self.pipeline = Pipeline(self.output_dir, self.downloader)
    
    self.targets = self.load_targets(config_path)

  def load_targets(self, path):
    # if not os.path.exists(path):
    #   print(f"[!] Config file not found: {path}")
    #   return []
    # try:
    #   with open(path, 'r') as f:
    #       return json.load(f)
    # except Exception as e:
    #   print(f"[!] Config Error: {e}")
    #   return []

    if not os.path.exists(path):
      print(f"[!] Config file not found: {path}")
      return []
    
    targets = []
    try:
      with open(path, 'r', encoding='utf-8') as f:
        for line in f:
          line = line.strip()
          if line:
            targets.append(json.loads(line))
      return targets
    
    except json.JSONDecodeError as e:
      print(f"[!] JSON Format Error: {e}")
      try:
        with open(path, 'r', encoding='utf-8') as f:
          return json.load(f)
      except:
        return []
    except Exception as e:
      print(f"[!] Config Load Error: {e}")
      return []

  def worker(self, site):
    url = site.get('url')
    print(f"[*] Processing: {url}")
    
    response = self.downloader.fetch(url)
    if not response: 
      print(f"   [!] Skipped (Download Failed): {url}")
      return

    parser = PageParser(response.content, url)
    title, content = parser.extract_metadata()
    
    if not content:
      print(f"[-] No content extracted: {url}")
      return

    saved_images = []
    if site.get('image', False):
      image_urls = parser.extract_image_urls()
      print(f"   [*] Found {len(image_urls)} candidate images.")
      saved_images = self.pipeline.process_images(image_urls)

    article_data = {
      "url": url,
      "title": title,
      "content": content,
      "images": saved_images
    }
    self.pipeline.save_article(article_data)
    print(f"[✓] Finished: {title[:30]}...")

  def run(self, max_workers=5):
    if not self.targets:
      print("[!] No targets to scrape. Exiting.")
      return

    print(f"[*] Engine started with {len(self.targets)} targets.")
    print(f"[*] Saving data to: {self.output_dir}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
      executor.map(self.worker, self.targets)
    
    print("[*] All tasks completed.")