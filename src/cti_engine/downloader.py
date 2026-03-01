import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import random

class Downloader:
  def __init__(self):
    self.session = requests.Session()

    self.user_agents = [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]

    # Retry Strategy ( 3 times, with backofff)'
    retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)

    self.session.mount('http://', adapter) 
    self.session.mount('https://', adapter)

    # self.session.headers.update({
    #   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    # })

  def fetch(self, url):
    try:
      time.sleep(random.uniform(1.0, 3.0))
      headers = {
        "User-Agent": random.choice(self.user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/"
      }
      response = self.session.get(url, headers=headers,timeout=5)
      response.raise_for_status()
      return response
    except requests.exceptions.HTTPError as e:
      if e.response.status_code == 429:
        print(f"   [!] Rate Limited (429) by Google. Slowing down...")
        time.sleep(5)
      else:
        print(f"   [!] HTTP Error: {url} - {e}")
      return None
    except requests.exceptions.RequestException as e:
      print(f"[*] Network Error: {url} - {e}")
      return None
    