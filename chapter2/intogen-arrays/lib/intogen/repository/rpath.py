
def absolute(path):
	if len(path) == 0 or path[0] != "/":
		path = "/" + path
	return path

def clean(path, absolute = False):
	if absolute:
		cpath = ["/"]
		last_char = "/"
	else:
		cpath = []
		last_char = ""

	for ch in path:
		if last_char == "/" and ch == "/":
			continue

		last_char = ch
		cpath += [ch]

	return "".join(cpath)

def join(*paths):
	jpath = [p for p in paths if p is not None and len(p) > 0]
	return clean("/".join(jpath))