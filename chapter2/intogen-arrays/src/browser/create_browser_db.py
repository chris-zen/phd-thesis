import parser
import os
import os.path
import glob

from tempfile import mkstemp
from subprocess import Popen

from optparse import OptionParser

parser = OptionParser(usage = "usage: %prog [options] <SQL scripts path>", add_help_option = False)

parser.add_option("--help", action="store_true", dest="help", default=False)

parser.add_option("--mysql", dest="mysql", default="mysql", help="Default mysql binary")

parser.add_option("--browser-db", dest="browser_db", default=None, metavar="NAME",
	help="Browser database name")

parser.add_option("--biomart-db", dest="biomart_db", default=None, metavar="NAME",
	help="Biomart database name")

parser.add_option("--start", dest="start_file", default=None, metavar="NAME",
	help="SQL file to start with. Optional")

parser.add_option("-h", "--host", dest="db_host", default=None, metavar="HOST", help="host")
parser.add_option("-P", "--port", dest="db_port", default=None, metavar="PORT", help="port")
parser.add_option("-u", "--user", dest="db_user", default=None, metavar="NAME", help="user name")
parser.add_option("-p", "--passwd", dest="db_passwd", default=None, metavar="PASSWD", help="password")

(options, args) = parser.parse_args()

if options.help:
	parser.print_help()

if len(args) != 1:
	parser.error("Incorrect number of arguments")

if options.browser_db is None:
	parser.error("Missing browser database name option")

if options.biomart_db is None:
	parser.error("Missing biomart database name option")

files = sorted(glob.glob(os.path.join(args[0], "*.sql")))

start = 0

if options.start_file is not None:
	start_file = os.path.abspath(options.start_file)
	while start < len(files) and os.path.abspath(files[start]) != start_file:
		start += 1

for i in range(start, len(files)):
	file = files[i]
	
	print "Executing {} ...".format(file)

	sql = open(file, "r").read()
	sql = sql.format(**{
			"browser_db" : options.browser_db,
			"biomart_db" : options.biomart_db })

	tmp_file = mkstemp()[1]
	tmp = open(tmp_file, "w")
	tmp.write(sql)
	tmp.close()

	sb = [options.mysql]
	if options.db_host is not None:
		sb += ["-h", options.db_host]
	if options.db_port is not None:
		sb += ["-P", options.db_port]
	if options.db_user is not None:
		sb += ["-u", options.db_user]
	if options.db_passwd is not None:
		sb += ["-p{}".format(options.db_passwd)]
	sb += [options.browser_db]

	cmd = " ".join(sb)

	#print cmd

	process = Popen(cmd, stdin = open(tmp_file, "r"), shell = True)

	retcode = process.wait()

	os.remove(tmp_file)

	if retcode != 0:
		exit(retcode)
