import asyncio
import json
import os
from tqdm.asyncio import tqdm

async def file_writer_worker(queue, output_path):
  print(f"[*] Writer service started for {output_path}")

  with open(output_path, 'a', encoding="utf-8") as f_out:
    while True:
      item = await queue.get()

      if item is None:
        queue.taks_done()
        break

    try:
      f_out.write(json.dumps(item) + '\n')
      f_out.flush()
    
    except Exception as e:
      print(f"[*] Error writing to file: {e}")

    finally:
      queue.task_done()
  
  print("[*] Writer service stopped.")


async def data_processor_worker(sem, generator, data, queue):
  max_retries = 3
  retry_delay = 5

  async with sem:
    for attempt in range(max_retries + 1):
      try:
        result = await asyncio.to_thread(generator.convert_cot_dataset, data['input'])

        if result:
          output_str = f'### Reasoning:\n{result.get('cot')}\n\n### Name Entity:\n{result.get('name_entities')}\n\n### Relationship:\n{result.get('relationships')}'
          processed_item = {
            'instruction': data['instruction'],
            'input': data['input'],
            'output': output_str
          }
          await queue.put(processed_item)
          return
        
      except Exception as e:
        if attempt < max_retries:
          print(f"[*] Error on item (Attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying i {retry_delay}s...")
          await asyncio.sleep(retry_delay)
        else:
          print(f"[*] Failed item after {max_retries + 1} attempts: {e}")