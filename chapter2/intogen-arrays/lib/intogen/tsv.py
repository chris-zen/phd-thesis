
def filter_columns(inpf, outf, columns, new_column_names=None, header=True, sep="\t"):
	has_indices = sum([1 for x in columns if isinstance(x, int)]) == len(columns)

	if header:
		hdr = inpf.readline().rstrip().split(sep)
		if not has_indices:
			cindices = []
			hdr_index = {}
			for i, name in enumerate(hdr):
				hdr_index[name] = i
			for c in columns:
				if c not in hdr_index:
					raise Exception("Column '%s' not found in header [%s]" % (c, ", ".join(hdr)))
				cindices += [hdr_index[c]]
			column_indices = cindices
		else:
			column_indices = columns
	elif not has_indices:
		raise Exception("filter_columns with columns indices expected")

	if header and not has_indices:
		if new_column_names is None:
			new_column_names = columns

		outf.write(sep.join(new_column_names))
		outf.write("\n")

	count = 0
	for line in inpf:
		d = line.rstrip().split(sep)
		outf.write(sep.join([d[index] for index in column_indices]))
		outf.write("\n")
		count += 1

	return count
