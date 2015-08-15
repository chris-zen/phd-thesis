import urllib
import urllib2

from lxml import etree

class Pubmed():
	def __init__(self):
		self.__url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

	def find(self, pmid):
		if isinstance(pmid, basestring):
			pmid = [pmid]
		pmid = ",".join(pmid)

		data = urllib.urlencode({"db" : "pubmed", "id" : pmid, "retmode" : "xml"})
		req = urllib2.Request(self.__url, data)
		response = urllib2.urlopen(req)
		doc = etree.parse(response, etree.XMLParser(encoding="utf-8"))
		root = doc.getroot()

		articles = []
		for a in root.findall("PubmedArticle"):
			a = a.find("MedlineCitation/Article")
			if a is not None:
				article = {}
				article["title"] = a.findtext("ArticleTitle")
				article["journal"] = a.findtext("Journal/Title")
				article["volume"] = a.findtext("Journal/JournalIssue/Volume")
				article["issue"] = a.findtext("Journal/JournalIssue/Issue")

				pubdate = a.find("Journal/JournalIssue/PubDate")
				if pubdate is not None:
					year = pubdate.findtext("Year")
					month = pubdate.findtext("Month")
					day = pubdate.findtext("Day")
					if year is not None:
						if month is not None:
							if day is not None:
								if len(day) < 2:
									day = ("0" * (2 - len(day))) + day
								date = "{0}-{1}-{2}".format(year, month, day)
							else:
								date = "{0}-{1}".format(year, month)
						else:
								date = "{0}".format(year)
					else:
						date = ""
				else:
					date = ""

				article["date"] = date

				authors = []
				for auth in a.find("AuthorList"):
					last_name = auth.findtext("LastName")
					initials = auth.findtext("Initials")
					if last_name:
						if initials:
							authors += [last_name + " " + initials]
						else:
							authors += [last_name]

				if len(authors) > 0:
					if len(authors) > 1:
						article["short_authors"] = authors[0] + " et al"
					else:
						article["short_authors"] = authors[0]
				else:
					article["short_authors"] = ""

				article["authors"] = authors

				for k,v in article.items():
					if v is not None and isinstance(v, basestring):
						article[k] = v.strip()
					#else:
					#	article[k] = ""

				articles += [article]

		return articles

def find(pmid):
	return Pubmed().find(pmid)