"""Run from backend: ../.venv/bin/python ../scripts/verify_embeddings.py"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.embedding_service import embed

vectors = [embed(text) for text in (
    'Python FastAPI SQL backend engineer',
    'Python developer building SQL APIs',
    'Landscape gardener planting trees',
)]
a, b, c = vectors
similar = sum(x*y for x,y in zip(a,b))
unrelated = sum(x*y for x,y in zip(a,c))
assert len(a) == 384
assert abs(math.sqrt(sum(x*x for x in a)) - 1) < 0.001
assert similar > unrelated
print({'dimensions': len(a), 'norm': math.sqrt(sum(x*x for x in a)),
       'related_similarity': similar, 'unrelated_similarity': unrelated})
