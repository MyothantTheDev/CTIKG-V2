import os
import argparse
import sys
import asyncio

from utils.hashing import get_item_hash, get_processed_hashed
from utils.datapipeline import load_input_data
from utils.workers import data_processor_worker, file_writer_worker
from tqdm.asyncio import tqdm
from cti_engine.engine import CTI_Engine

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT)

from core.augmentation import DataGenerator
from dotenv import load_dotenv

MODEL_NAME = "gemini-2.5-flash"

def run_spider(input_file:str = None, output_file: str =None, workers: int = 5):
  if not os.path.exists(input_file):
    print(f"[!] Error: Input file '{input_file} not found.")
    sys.exit(1)
  
  try:
    engine = CTI_Engine(input_file, output_file)
    engine.run(workers)
  except KeyboardInterrupt:
    print("\n[!] Scraper stopped by user.")
    sys.exit(0)
  except Exception as e:
    print(f"[!] Unexpected Error: {e}")

  print('[*] Crawling Finished.')

  
async def run_cot_augmentation(input_path, output_path):
  concurrency_limit = 5

  print('[*] Starting CoT Augmentation...')
  print(f'[*] Input: {input_path}')
  print(f'[*] Output: {output_path}')

  if not os.path.exists(input_path):
    print(f'[!] Error: Input file not found: {input_path}')
    return
  
  try:
    generator = DataGenerator()
    print('[*] Generator initialized. Processing data...')

    all_data = load_input_data(input_path)
    print(f'[*] Total Input Items: {len(all_data)}')

    processed_hashes = get_processed_hashed(output_path)
    pending_items = []
    skipping_count = 0

    for item in all_data:
      h = get_item_hash(item)

      if h in processed_hashes:
        skipping_count += 1
      
      else:
        item['_hash'] = h
        pending_items.append(item)

    print(f'[*] Skipped: {skipping_count} items (Already done).')
    print(f'[*] Remaining: {len(pending_items)} items to process.')

    if not pending_items:
      print(f'[*] Nothing to process. Exiting.')
      return
    
    queue = asyncio.Queue()
    sem = asyncio.Semaphore(concurrency_limit)

    writer_task = asyncio.create_task(file_writer_worker(queue, output_path))

    tasks = [
      data_processor_worker(sem, generator, item, queue)
      for item in pending_items
    ]

    await tqdm.gather(*tasks, desc="Augmenting")

    await queue.put(None)
    await queue.join()

    await writer_task

    print(f"[*] Process Completed Successfully! Saved to {output_path}")

  except Exception as e:
    print(f'[*] Critical Error in Main Process: {e}')


def main():
  env = os.path.join(ROOT, '.env')
  if not load_dotenv(env):
    raise ValueError("[*] Environment variable cannot load.")
  
  parser = argparse.ArgumentParser(description="CTI Knowledge Graph Pipeline Tool")

  subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

  crawl_parser = subparsers.add_parser('crawl', help='Run the web spider')
  crawl_parser.add_argument(
    '-i', '--input',
    type=str,
    required=True,
    help="Path to the input JSON config file (e.g., data/targest.json)"
  )
  crawl_parser.add_argument(
    '-o', '--output',
    type=str,
    required=True,
    help='Optional output file path (e.g. data/scraped.json). If not provided, saves to DB.'
  )
  crawl_parser.add_argument(
    '-w', '--workers',
    type=int,
    default=5,
    help="Number of concurrent worker threads (Default: 5)"
  )

  cot_parser = subparsers.add_parser('cot', help='Run Chain-of-Though augmentation.')
  cot_parser.add_argument(
    '-i', '--input',
    type=str,
    required=True,
    help='Input raw dataset path (JSON)'
  )
  cot_parser.add_argument(
    '-o', '--output',
    type=str,
    help='Output fine-tuning dataset path (JSONL)'
  )

  args = parser.parse_args()

  match args.command:
    case 'crawl':
      run_spider(args.input, args.output, args.workers)

    case 'cot':
      asyncio.run(run_cot_augmentation(input_path=args.input, output_path=args.output))

    case _:
      print(f'[*] Supported arguments are crawl and cot. {args.output}')


if __name__ == "__main__":
  main()