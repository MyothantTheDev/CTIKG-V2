import sqlite3
from typing import Dict
import os


class DatabaseManager:
  def __init__(self, db_path: str):
    self.db_path = db_path
    self.conn = None
    self.cursor = None
    self._create_directory()
    self._connect()
    self._init_table()

  def _create_directory(self):
    dir = os.path.dirname(self.db_path)
    if dir and not os.path.exists(dir):
      try:
        os.mkdir(dir)
        print(f"[*] Folder created at {dir}")
      except OSError as e:
        print(f"[*] Error creating directory: {e}")
    
  def _connect(self):
    self.conn = sqlite3.connect(self.db_path)
    self.cursor = self.conn.cursor()

  def _init_table(self):
    self.cursor.execute("""
      CREATE TABLE IF NOT EXISTS articles (
        url TEXT PRIMARY KEY,
        title TEXT,
        content TEXT,
        image_path TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    self.conn.commit()

  def url_exists(self, url: str) -> bool:
    self.cursor.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    return self.cursor.fetchone() is not None
  
  def insert_article(self, article_data: Dict):
    try:
      self.cursor.execute("""
        INSERT INTO articles (url, title, content, image_path) 
        VALUES (?, ?, ?, ?)
      """, (
      article_data["url"],
      article_data["title"],
      article_data["content"],
      article_data["image_path"]
      ))
      self.conn.commit()
      return True
    except Exception as e:
      print(f"DB Error: {e}")
      return False
    
  def fetch_articles_with_pdfs(self):
    self.cursor.execute("SELECT url, files_path, content FROM articles WHERE files_path != ''")
    return self.cursor.fetchall()
  
  def fetch_all_content(self):
    self.cursor.execute("SELECT url, content FROM articles WHERE content IS NOT NULL")
    return self.cursor.fetchall()
  
  def update_article_content(self, new_content: str, url: str):
    self.cursor.execute("UPDATE article SET content = ? WHERE url = ?", (new_content, url))
    self.conn.commit()

  def close(self):
    if self.conn:
      self.conn.close()