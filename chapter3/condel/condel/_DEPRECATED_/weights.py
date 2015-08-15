import json

def load_weights(path):
	with open(path) as f:
		state = json.load(f)

	return state

def save_weights(path, state, reduced=False):
	with open(path, "w") as f:
		json.dump(state, f, indent=True)