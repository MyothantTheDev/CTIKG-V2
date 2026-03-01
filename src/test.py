from cti_engine.engine import CTI_Engine

input_file = '/work/experiment/ctikg-v2.0.0/src/test.jsonl'
output_file = '/work/experiment/ctikg-v2.0.0/data/processed'
workers = 1
engine = CTI_Engine(input_file, output_file)
engine.run(workers)