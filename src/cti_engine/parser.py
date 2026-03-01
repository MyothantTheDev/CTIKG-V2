from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urljoin

class PageParser:
  def __init__(self, html_content, base_url):
    # lxml parser is faster and more lenient than html.parser
    self.soup = BeautifulSoup(html_content, 'lxml')
    self.base_url = base_url
    self.html_content = html_content

  def extract_metadata(self):
    title = self.soup.title.string.strip() if self.soup.title else "No Title"
    text = trafilatura.extract(self.html_content)
    return title, text
  
  def extract_image_urls(self):
    """Smart extraction: Priortize <article> or <main>"""
    images = []

    manual_xpaths = self.config.get('image', [])
    if manual_xpaths and isinstance(manual_xpaths, list):
      # print(f"   [⚙️] Using Manual XPaths ({len(manual_xpaths)} rules)")
      for xpath_query in manual_xpaths:
        try:
          results = self.tree.xpath(xpath_query)
          for item in results:
            link = None

            if isinstance(item, str):
              link = item
            elif hasattr(item, 'get'):
              link = item.get('src') or item.get('data-src') or item.get('data-original')

            if link:
              full_url = urljoin(self.base_url, link.strip())
              images.append(full_url)
        
        except Exception as e:
          print(f"   [!] XPath Error for '{xpath_query}': {e}")

      if images:
        return list(set(images))
      
    return list(set(images))
    # targets = [
    #   self.soup.find('article'),
    #   self.soup.find('main'),
    #   self.soup.find(class_='post-content'),
    #   self.soup.find(class_='entry-content'),
    #   self.soup.find(id='content')
    # ]

    
    # content_area = next((t for t in targets if t), self.soup.body)
    
    # if not content_area: 
    #   print("   [!] No content container found.")
    #   return []

    # images = []
    # for img in content_area.find_all('img'):
    #   possible_sources = [
    #     img.get('src'),
    #     img.get('data-src'),
    #     img.get('data-original'),
    #     img.get('data-url'),
    #     img.get('data-lazy-src')
    #   ]
    #   src = next((link for link in possible_sources if link), None)
    #   if not src: continue
      
    #   src_lower = src.lower()
      
    #   if src_lower.startswith('data:image'):
    #     real_src = img.get('data-src') or img.get('data-original')
    #     if real_src:
    #       src = real_src
    #     else:
    #       continue

    #   if '.svg' in src_lower: continue

    #   if any(x in src_lower for x in ['logo', 'icon', 'avatar', 'facebook', 'twitter']): continue

    #   full_url = urljoin(self.base_url, src)
    #   images.append(full_url)
        
    # return list(set(images))