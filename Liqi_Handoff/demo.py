import argparse
import json
import sys
from pathlib import Path
from liqi_draft import DraftRecommender


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--request',type=Path)
    p.add_argument('--heroes',action='store_true')
    args=p.parse_args()
    try:
        service=DraftRecommender()
        if args.heroes:
            result=service.heroes()
        elif args.request:
            result=service.recommend(json.loads(args.request.read_text(encoding='utf-8-sig')))
        else:
            p.error('Specify --request FILE or --heroes')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as exc:
        print(json.dumps({'error':'invalid_request_or_package','message':str(exc)},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)


if __name__=='__main__': main()
