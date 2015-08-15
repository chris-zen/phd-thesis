from pymongo import MongoClient
import pymongo.uri_parser

def mongodb_from_uri(uri, db_name=None):
	parsed_uri = pymongo.uri_parser.parse_uri(uri)
	db_name = parsed_uri.get("database", db_name)
	conn = MongoClient(uri)
	db = conn[db_name]
	return db