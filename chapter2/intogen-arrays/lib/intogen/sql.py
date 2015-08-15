
class BatchInsert(object):
	"""Helper to do batch inserts"""
	
	def __init__(self, cursor, table, columns = None, batch_size = 1000, lock_table = None):
		self.__cursor = cursor
		self.table = table
		self.columns = columns

		if columns is not None:
			self.__insert_sql = u"INSERT INTO {} ({}) VALUES".format(table, ", ".join(columns))
		else:
			self.__insert_sql = u"INSERT INTO {} VALUES".format(table)

		self.batch_size = batch_size

		if lock_table is not None:
			lock_table = lock_table.upper()
			if lock_table not in ["READ", "WRITE"]:
				raise Exception("lock_table should be one of READ or WRITE")
		
		self.lock_table = lock_table

		self.count = 0
		self.__sql = []

		if self.lock_table is not None:
			self.__cursor.execute("LOCK TABLES {} {}".format(self.table, self.lock_table))

	def __execute(self):
		if len(self.__sql) == 0:
			return

		sql = u"".join(self.__sql).encode("utf-8", "replace")
		#print sql

		self.__cursor.execute(sql)
		#print "Affected rows: {0}".format(self.__cursor.rowcount)

	def __marshall_data(self, data):
		sb = []
		for v in data:
			if v is None:
				sb += [u"NULL"]
			elif isinstance(v, basestring):
				sb += [u"'" + v + u"'"]
			else:
				sb += [str(v)]

		return u",".join(sb)

	def insert(self, *data):
		if self.count % self.batch_size == 0:
			self.__execute()

			self.__sql = [self.__insert_sql, u"\n\t(", self.__marshall_data(data), u")"]
		else:
			self.__sql += [u",\n\t(", self.__marshall_data(data), u")"]

		self.count += 1

	def close(self):
		self.__execute()

		if self.lock_table is not None:
			self.__cursor.execute("UNLOCK TABLES")