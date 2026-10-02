import argparse
import json
from pathlib import Path
from .core import evaluate
from .providers import provider

def main():
    p=argparse.ArgumentParser(description='Run an evaluation and fail CI below a required pass rate.')
    p.add_argument('dataset');p.add_argument('prompt');p.add_argument('--provider',choices=['replay','bedrock','http'],default='replay');p.add_argument('--min-pass-rate',type=float,default=1);p.add_argument('--output')
    args=p.parse_args()
    try:
        if not 0<=args.min_pass_rate<=1:raise ValueError('Minimum pass rate must be 0–1.')
        result=evaluate(json.loads(Path(args.dataset).read_text()),json.loads(Path(args.prompt).read_text()),provider(args.provider))
        text=json.dumps(result,indent=2)
        if args.output:Path(args.output).write_text(text+'\n')
        print(text);return int(result['pass_rate']<args.min_pass_rate or result['error_count']>0)
    except (ValueError,OSError) as error:print(json.dumps({'error':str(error)}));return 2
if __name__=='__main__':raise SystemExit(main())
