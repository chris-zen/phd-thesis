from io import FileReader, FileWriter

def __open_reader(f):
	fpath = None
	if isinstance(f, str) or isinstance(f, unicode):
		fpath = f
		f = FileReader(f)
	return f, fpath

def __open_writer(f):
	fpath = None
	if isinstance(f, str) or isinstance(f, unicode):
		fpath = f
		f = FileWriter(f)
	return f, fpath

def __close(f, path):
	if path is not None:
		f.close()

def __read_header(f, dtypes = None):
	if dtypes is None:
		dtypes = {}

	hdr = {}
	line = f.readline().lstrip()
	while len(line) > 0 and line[0] == '#':
		line = f.readline().lstrip()

	fields = line.rstrip().split("\t")
	for index, h in enumerate(fields):
		if len(h) > 2 and h[0] == '"' and h[-1] == '"':
			h = h[1:-1]
		dtype = dtypes[h] if h in dtypes else str
		hdr[h] = (index, dtype)

	return hdr

def __read_data(line, hdr, key_fields, fields):
	data = []
	l = line.rstrip().split("\t")

	ret = []
	for kf in key_fields:
		index, dtype = hdr[kf]
		d = l[index]
		if len(d) > 2 and d[0] == '"' and d[-1] == '"':
			d = d[1:-1]
		ret += [d]

	for field in fields:
		index, dtype = hdr[field]
		d = l[index]
		if len(d) > 2 and d[0] == '"' and d[-1] == '"':
			d = d[1:-1]
		if dtype == float and d == "-":
			d = 'nan'
		data += [dtype(d)]

	ret += [data]

	return tuple(ret)

def drepr(d):
	if d is None:
		return "-"

	if isinstance(d, float):
		s = str(d)
		if s.endswith(".0"):
			return s[:-2]
		else:
			return s
	else:
		return str(d)

def read_header_names(f):
	f, fpath = __open_reader(f)

	line = f.readline().lstrip()
	while len(line) > 0 and line[0] == '#':
		line = f.readline().lstrip()

	__close(f, fpath)

	return tuple(line.rstrip().split("\t"))

def __default_flatten_header_name_func(col, field):
	return "_".join([col, field.replace("-", "_").lower()])

def flatten(inpf, outpf, dtypes, fields, header_name_func = __default_flatten_header_name_func):

	inpf, inp_path = __open_reader(inpf)
	outpf, outp_path = __open_writer(outpf)

	key_fields = ["column", "row"]

	results = dict()
	col_ids = set()
	row_ids = set()
	hdr = __read_header(inpf, dtypes)
	for line in inpf:
		col_id, row_id, d = __read_data(line, hdr, key_fields, fields)
		col_ids.add(col_id)
		row_ids.add(row_id)
		if col_id in results:
			col_results = results[col_id]
		else:
			results[col_id] = col_results = dict()
		col_results[row_id] = d

	if len(results) == 0:
		return

	sorted_col_ids = sorted(col_ids)
	outpf.write("id")
	for col_id in sorted_col_ids:
		outpf.write("\t")
		outpf.write("\t".join([header_name_func(col_id, f) for f in fields]))
	outpf.write("\n")

	for row_id in sorted(row_ids):
		outpf.write(row_id)
		for col_id in sorted_col_ids:
			outpf.write("\t")
			d = results[col_id]
			if row_id in d:
				d = d[row_id]
				outpf.write("\t".join([drepr(x) for x in d]))
			else:
				outpf.write("\t".join(["-"] * len(fields)))
		outpf.write("\n")

	__close(inpf, inp_path)
	__close(outpf, outp_path)

def __default_column_and_attr_func(name):
	pos = name.find("_")
	if pos == -1:
		return (None, None)

	return (name[0:pos], name[pos + 1:])

def unflatten(inpf, outpf, row_column, column_and_attr_func = __default_column_and_attr_func):

	inpf, inp_path = __open_reader(inpf)
	outpf, outp_path = __open_writer(outpf)

	# process header

	hdr = inpf.readline().rstrip().split("\t")

	columns_map = {}
	attrs_map = {}

	hdr_desc = {}
	row_index = -1
	for index, name in enumerate(hdr):
		if name == row_column:
			row_index = index
			continue

		col_id, attr_id = column_and_attr_func(name)
		if col_id is None:
			continue

		if col_id not in columns_map:
			columns_map[col_id] = len(columns_map)
		if attr_id not in attrs_map:
			attrs_map[attr_id] = len(attrs_map)

		if col_id not in hdr_desc:
			hdr_desc[col_id] = {}
		col_desc = hdr_desc[col_id]
		if attr_id not in col_desc:
			col_desc[attr_id] = index

	if row_index == -1:
		raise Exception("row_column '{0}' not found in the header: {1}".format(row_column, ", ".join(hdr)))

	# process data

	columns = sorted(columns_map, key = lambda k: columns_map[k])
	attrs = sorted(attrs_map, key = lambda k: attrs_map[k])

	outpf.write("column\trow\t")
	outpf.write("\t".join(attrs))
	outpf.write("\n")

	for line in inpf:
		d = line.rstrip().split("\t")
		for col_id in columns:
			col_desc = hdr_desc[col_id]
			values = []
			for attr_id in attrs:
				if attr_id not in col_desc:
					values += [""]
					continue

				values += [d[col_desc[attr_id]]]

			outpf.write("\t".join([col_id, d[row_index]]))
			for v in values:
				outpf.write("\t")
				outpf.write(v)

			outpf.write("\n")

	__close(inpf, inp_path)
	__close(outpf, outp_path)

	return tuple(["column", "row"] + attrs)

def filter_attrs(inpf, outf, attr_names, new_attr_names=None):
	if new_attr_names is not None and len(attr_names) != len(new_attr_names):
		raise Exception("attr_names and new_attr_names has different lengths")

	inpf, inp_path = __open_reader(inpf)
	outpf, outp_path = __open_writer(outpf)

	hdr = inpf.readline().rstrip().split("\t")
	cindices = []
	hdr_index = {}
	for i, name in enumerate(hdr):
		hdr_index[name] = i
	for c in attr_names:
		if c not in hdr_index:
			raise Exception("Column '{0}' not found in header [{1}]".format(c, ", ".join(hdr)))
		cindices += [hdr_index[c]]
	attr_indices = cindices

	if new_attr_names is None:
		new_attr_names = attr_names

	outf.write(sep.join(new_attr_names))
	outf.write("\n")

	for line in inpf:
		d = line.rstrip().split("\t")
		outf.write("\t".join([d[index] for index in attr_indices]))
		outf.write("\n")

	__close(inpf, inp_path)
	__close(outpf, outp_path)

def append(outpf, inpf, ref_hdr, column_name_func = lambda name: name):

	inpf, inp_path = __open_reader(inpf)
	outpf, outp_path = __open_writer(outpf)

	hdr = __read_header(inpf)
	hdr = tuple(sorted(hdr, key = lambda k: hdr[k][0]))

	if hdr != ref_hdr:
		raise Exception("Can't append, files with different headers:\n{0}\n{1}".format(", ".join(ref_hdr), ", ".join(hdr)))

	try:
		col_index = ref_hdr.index("column")
	except:
		raise Exception("column label header not found")

	for line in inpf:
		d = line.rstrip().split("\t")
		d[col_index] = column_name_func(d[col_index])
		outpf.write("\t".join(d))
		outpf.write("\n")

	__close(inpf, inp_path)
	__close(outpf, outp_path)
