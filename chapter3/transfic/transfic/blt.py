import json

def load_blt_stats(path):
	with open(path) as f:
		doc = json.load(f)
		blt_stats = doc["blt"]
	return blt_stats