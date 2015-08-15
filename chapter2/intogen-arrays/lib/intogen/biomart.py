import MySQLdb

from intogen.io import FileReader

DEFAULT_INSERT_SIZE = 1000
DEFAULT_DB_ENGINE = "InnoDB"

ID_TYPE_TO_TABLE_INFIX = {
	"ensembl:gene" : "gene",
	"kegg:pathway"	: "kegg",
	"go:bp"			: "go",
	"go:mf"			: "go",
	"go:cl"			: "go",
	"transfac:tfbs" : "tfbs",
	"mirna:target"	: "mirna" }

def biomart_db_connect(db_conf, log):
	try:
		if "port" in db_conf:
			conn = MySQLdb.connect(
					host = db_conf.get("host", "localhost"),
					port = int(db_conf["port"]),
					user = db_conf.get("user"),
					passwd = db_conf.get("passwd"),
					db = db_conf["name"])
		else:
			conn = MySQLdb.connect(
					host = db_conf.get("host", "localhost"),
					user = db_conf.get("user"),
					passwd = db_conf.get("passwd"),
					db = db_conf["name"])
		conn.autocommit(1)
		return conn
	except MySQLdb.Error:
		log.error("Error connecting with the database")
		raise

def map_from_select(cursor, select):
	map = {}
	cursor.execute(select)
	row = cursor.fetchone()
	if row is None:
		return map
	
	row_len = len(row)
	if row_len < 2:
		raise Exception("Unexpected number of fields for query: {0}".format(select))
	elif row_len == 2:
		while row:
			map[row[1]] = row[0]
			row = cursor.fetchone()
	else:
		while row:
			map[tuple(row[1:])] = row[0]
			row = cursor.fetchone()
	return map

def map_from_file(path):
	map = {}
	f = FileReader(path)
	for line in f:
		line = line.rstrip()
		fields = line.split("\t")
		if len(fields) != 2:
			raise Exception("Unexpected number of columns: ({0})".format(", ".join(fields)))
		map[fields[0]] = fields[1]
	f.close()
	return map