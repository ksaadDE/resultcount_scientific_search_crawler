#!/usr/bin/python3
"""
Written 2023-06-10 to 2023-06-13
Downloads results from arxiv.org and base-search.net (getSources method) by searchTerm and Date
"""
import requests_cache
import bs4
import datetime
import csv
from datetime import tzinfo
from datetime import timedelta
import matplotlib.pyplot as plt

def getSources() -> list:
	return ["arxiv", "base"]

def getCurrentYear() -> int:
	return datetime.date.today().year

def getUrl(sourceName:str="arxiv", searchTerm:str="Steganography", year:int=2023) -> str:
	assert year >= datetime.MINYEAR and year <= getCurrentYear()+2, "Year must be between the bounds of '{}' and '{}'".format(datetime.MINYEAR, getCurrentYear()+2)
	match sourceName:
		case 'arxiv':
			return "https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term={0}&terms-0-field=all&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=specific_year&date-year={1}&date-from_date={1}-01-01&date-to_date={1}-12-31&date-date_type=submitted_date&abstracts=hide&size=50&order=-submitted_date".format(
				# url parameters
				searchTerm,
				year
			)
		case 'base':
			return 'https://www.base-search.net/Search/Results?type=all&lookfor={}+year%3A{}&ling=0&oaboost=1&name=&thes=&refid=dcresde&newsearch=1'.format (
				searchTerm,
				year
			)
		case _:
			return ""

def getResults(url:str, proxyIP:str="127.0.0.1", proxyPort:int="9050") -> str:
	assert len(url) > 10, 'URL must be gt 10 in length'
	assert "https" in url, 'URL must be https'
	
	#print("[+] crawling '{}'".format(url))
	session = requests_cache.CachedSession('demo_cache', expire_after=timedelta(days=1))

	session.proxies = {
		'http': 'socks5://{}:{}'.format(proxyIP, proxyPort),
		'https': 'socks5://{}:{}'.format(proxyIP, proxyPort),
	}

	r=session.get(url)
	return r.text

def processArxivResults(data:str) -> int:
	assert len(data) > 100, 'data length must be gt 100'
	assert 'class="title' in data, 'data must contain the element that contains the class title'

	soup = bs4.BeautifulSoup(data, features="lxml")
	divs=soup.find_all("h1", class_="title")
	assert len(divs) > 0, 'Found divs must be gt 0'

	if "Sorry, your query returned no results" in divs[0].text.strip():
		#raise Exception("No results")
		return 0

	if "Whoops! Something went wrong" in divs[0].text.strip().replace ("\n",""):
		raise Exception ("err: Whoops! Something went wrong. Please correct errors in the form below.")
		return 0


	try:
		return int(divs[0].text.strip().split("of")[1].strip().split(" ")[0].replace(",",""))
	except Exception as e:
		print("[-] ERROR: ", e)
		print(divs[0].text)
		return 0

def processBaseResults(data:str) -> int:
	assert len(data) > 100, 'data length must be gt 100'

	if "No documents found." in data:
		#raise Exception ("no data found")
		return 0

	if not  'class="heading' in data:
		#print(data)
		#raise Exception ("no heading found = no data found")
		return 0
	#assert, 'data must contain the element that contains the class heading'

	soup = bs4.BeautifulSoup(data, features="lxml")
	divs=soup.find_all("div", class_="heading")
	if len(divs) == 0:
		raise Exception ("Divs Length is 0, but must be > 0")
		return 0

	try:
		return int(divs[0].text.strip().replace("\n","").replace("\r","").replace("\t","").split("in")[0].strip().split(" ")[0].replace(",",""))
	except Exception as e:
		print("[-] ERROR: ", e)
		print(divs[0].text)
		return 0

def processResults(sourceName:str, data:str) -> int:
	assert isAllowedSource(sourceName), "source '{}' must be allowed".format(sourceName)

	match sourceName:
		case 'arxiv':
			return processArxivResults (data)
		case 'base':
			return processBaseResults(data)

def isAllowedSource (sourceName:str) -> bool:
	assert len(sourceName) > 0, 'sourceName must be given'
	return any([sourceName.lower() == source.lower() for source in getSources()])

def downloadResultsForYear(sourceName:str="", searchTerm:str="Steganography", year:int=2023) -> dict:
	assert isAllowedSource(sourceName), 'sourceName must be allowed'

	try:
		assert not int(searchTerm.replace(",","")), 'searchTerm must be a string (= not a integer)'
	except Exception as e:
		eMsg = str(e)
		if "literal" in eMsg or "base 10" in eMsg:
			pass
		else:
			raise Exception ("searchTerm in downloadResults is wrong")

	url=getUrl(sourceName, searchTerm, year)
	print("[+] URL for source :'{}', searchTerm: '{}' and year: '{}' is '{}'".format(sourceName, searchTerm, year, url))
	data=getResults(url)
	results=processResults(sourceName, data)
	errMsg=""

	match sourceName:
		case 'arxiv':
			errMsg = "no results" if "returned no results"  in data or "Whoops! Something went wrong. Please correct errors in the form below." in data else ''
		case 'base':
			errMsg = "no results" if "Keine zu Ihrer Anfrage passenden Dokumente gefunden" in data else ''
	#print("[+] results:", results, "year:", year)

	return {
			"searchTerm": searchTerm,
			"year": year,
			"results":results,
			"errmsg": errMsg,
			"url": url
		}

def getArrIndexWithMaxElements(rows) -> int:
	arrI=0
	rowKeys=[x for x in rows]
	maxV=max([len(rowKeys) for row in rows])
	for i in range(0, len(rowKeys)):
		if len(rowKeys[i]) == maxV:
			return i
	return -1

def genChart(sourceName:str, data:list, fname:str="") -> bool:
	assert isAllowedSource(sourceName), "Source '{}' must be allowed"
	assert ".csv" in fname, 'fname must contain a .csv'
	fname=fname.replace(".csv", "_CHART.png")
	X = list([x['year'] for x in data ])
	Y = list([x['results'] for x in data])
	plt.bar(X, Y, color='g')
	plt.title("Results for search term '{}' per year (source:{})".format( data[0]['searchTerm'], sourceName))
	plt.xlabel("year")
	plt.ylabel("results")
	plt.savefig(fname)
	plt.close()
	return True

def writeData (data:list, fname:str=""):
	assert len(fname) > 5, 'Length of fname must be gt 5'
	assert ".csv" in fname, "fname must contain a '.csv'"
	with open(fname, 'w+', newline='') as csvfile:
		spamwriter = csv.DictWriter(csvfile, data[getArrIndexWithMaxElements(data)].keys() , delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
		spamwriter.writeheader()
		for row in data:
			spamwriter.writerow(row)
	print("[+] saved output to '{}'".format(fname))

#https://stackoverflow.com/a/23705687
class simple_utc(tzinfo):
	def tzname(self,**kwargs):
		return "UTC"
	def utcoffset(self, dt):
		return timedelta(0)

def getCurrentDateTimeStr(fFormat=True) -> str:
	dtStr:str = datetime.datetime.utcnow().replace(tzinfo=simple_utc()).isoformat()
	if fFormat:
		dtStr = dtStr.replace("-", "_")
		dtStr = dtStr.replace(":", "_")
		dtStr = dtStr.replace("+", "_tzPlus_")
		dtStr = dtStr.replace("-", "_tzMinus_")
	return dtStr

def downloadSearchTermAndSave(sourceName:str, searchTerm:str, fromYear:int, toYear:int, steps:int=1):
	assert isAllowedSource(sourceName), "Source '{}' must be allowed.".format(sourceName)

	currentDateTime:str = getCurrentDateTimeStr ()
	years=list(range(fromYear, toYear, 1))
	years.append(getCurrentYear())
	fname="{}_{}__{}_to_{}__{}.csv".format(sourceName,searchTerm, years[0], years[len(years)-1], currentDateTime)
	data=[downloadResultsForYear(sourceName,searchTerm, year) for year in years]
	writeData(data, fname)
	genChart(sourceName, data, fname)


"""
  examples (arxiv=prepints, base=scientific papers):
  - downloadSearchTermAndSave("base", "searchTerm", startyear, getCurrentYear(),1)
  - downloadSearchTermAndSave("arxiv", "searchTerm", startyear, getCurrentYear(),1)
"""
