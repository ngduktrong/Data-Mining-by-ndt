import json
from pathlib import Path
from recommender import load_model, recommend
ROOT = Path(__file__).resolve().parent
model = load_model(ROOT / 'model.json')
request = json.loads((ROOT / 'example_request.json').read_text(encoding='utf-8'))
print(json.dumps(recommend(model, **request), ensure_ascii=False, indent=2))
