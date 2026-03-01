import hashlib
import json
import os

def get_item_hash(data_dict: dict):
  """
  Generate Hash value for each dataset item
  """
  input_data = data_dict.get('input') or ''
  return hashlib.md5(input_data.encode('utf-8')).hexdigest()


def get_processed_hashed(output_path):
  """
  Return Set value that include Hash values from Output file or Empty Set
  """
  processed = set()
  if not os.path.exists(output_path):
    return processed
  
  print(f'[*] Reading existing progress from {output_path}...')
  with open(output_path, 'r', encoding='utf-8') as f:
    for line in f:
      line = line.strip()
      if line:
        try:
          data = json.loads(line)
          h = get_item_hash(data)
          processed.add(h)
        
        except Exception as e:
          print(f'[*] Facing error while reading output file: {e}')
          continue
  
  print(f'[*] Found {len(processed)} item already processed.')
  return processed
