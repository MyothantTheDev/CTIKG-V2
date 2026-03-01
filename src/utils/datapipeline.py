import json
import os

from pathlib import Path

def load_input_data(input_path: str):
  """
  Load Input Data. Return JSON Array or JSONL
  """
  if not os.path.exists(input_path):
    raise FileNotFoundError(f"Input file not found: {input_path}")
  
  data = []
  print(f"[*] Loading input data from {input_path}...")

  with open(input_path, 'r', encoding='utf-8') as f:
    content = f.read().strip()

    if content.startswith('[') and content.endswith(']'):
      try:
        data = json.loads(content)
        return data
      except json.JSONDecodeError:
        print("[*] Warning: File looks like JSON list but failed to parse. Trying JSONL...")

    lines = content.split('\n')
    for line in lines:
      line = line.strip()
      if line:
        try:
          data.append(json.loads(line))
        except json.JSONDecodeError:
          continue

  return data


def format_data(input_folder: str, output_file: str):
  path = Path(input_folder)
  if not path.exists():
    raise FileNotFoundError(f"[*] Error: {input_folder} is not found.")

  for file in path.iterdir():
    file_type = file.as_posix().split('.')

    if file_type[-1] == "mjson":

      with file.open('r', encoding='utf-8') as f:
        raw_data = json.loads(f.read())
        serialized = {
          'instruction': None,
          'input': raw_data['signal'],
          'output': None
        }

      with open(output_file, 'a') as f_out:
        f_out.write(json.dumps(serialized) + '\n')
        f_out.flush()

    else:
      continue