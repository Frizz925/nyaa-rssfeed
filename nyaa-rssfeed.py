#!/usr/bin/env python2.7

from funcslib import *
import os, sys, time
import urllib2

funcs = Functions(__file__)
json_dict = funcs.decodelocaljson()

class Cache(object):
	def __init__(self):
		self.dbfn = funcs.scriptfn.replace(".py", ".db")
		self.fn = os.path.join(funcs.scriptdir, self.dbfn)
		if not os.path.exists(self.fn):
			with open(self.fn, 'w') as f:
				f.write("")
				f.close()
			
	def read(self):
		result = []
		with open(self.fn) as f:
			for line in f:
				line = line.strip()
				if line:
					result.append(line)
			f.close()
		return result

	def append(self, input):
		with open(self.fn, 'a') as f:
			f.write(input + '\n')
			f.close()
cache = Cache()

class RSS(object):
	class Title(object):
		def __init__(self, html, index):
			self.html = html
			self.title = self.gettitle(index).encode('utf-8')
			self.link = self.getlink(index).encode('utf-8')
			
		def gettitle(self, start):
			end = self.html.find("</title>", start)
			return self.html[start:end]
			
		def getlink(self, index):
			start = self.html.find("<link>", index) + 6
			end = self.html.find("</link>", start)
			return self.html[start:end]

	def __init__(self, html, titles, tags):
		self.titles = []
		for index in self.getindexes(html, titles, tags):
			self.titles.append(self.Title(html, index))
			
	def getindexes(self, html, titles, tags):
		html = html.lower()
		html = html.replace("_", " ") # replace underscore with space to help with the search

		result = []
		found = []

		for title in titles:
			title = title.encode('utf-8')
			end = 0

			while True:
				start = html.find(title, end)

				if start != -1 and not start in found:
					start = html.rfind("<title>", 0, start)
					end = html.find("</title>", start)
					found.append(start + 7)

					for tag in tags:
						if tag in html[start:end]: # add to result if uploader tag is found in the title
							result.append(start + 7)
							break

				else:
					break
		return result

def main():
	# do sanity check
	if len(sys.argv) < 4:
		print "Not enough argument provided. (need at least 3)"
		sys.exit(1)

	if not sys.argv[1] in ["twitter", "twitter_test", "test"]:
		print "Unknown first argument."
		sys.exit(1)

	# decode json keys and register Twitter API
	if sys.argv[1] in ["twitter", "twitter_test"]:
		twitter_keys = [json_dict["app_keys"][0], json_dict["app_keys"][1], json_dict[sys.argv[1]][0], json_dict[sys.argv[1]][1]]
		twitter = funcs.twitter(twitter_keys)

	if sys.argv[2] == "update":
		if sys.argv[3] == "nyaa":
			url = "http://www.nyaa.eu/?page=rss"
		elif sys.argv[3] == "animetake":
			url = "http://animetake.com/feed/rss"
		else:
			url = sys.argv[3] # use provided url instead

		html = funcs.readpage(url) # read rss page
		html = funcs.unescape(html) # unescape characters
		rss = RSS(html, json_dict["titles"], json_dict["tags"]) # get list of titles

		for s in rss.titles:
			cached = s.title + " " + s.link

			# it has not been tweeted before (not found in the cache)
			if not cached in cache.read():
				if sys.argv[1] in ["twitter", "twitter_test"]:
					# append to cache in normal mode
					if sys.argv[1] == "twitter":
						cache.append(cached)

					# post tweet and sleep
					twitter.PostTweet(cached)
				else:
					funcs.printlog(cached)
		funcs.printlog("Exited successfully.")

	elif sys.argv[2] == "post":
		msg = " ".join(sys.argv[3:])

		if sys.argv[1] in ["twitter", "twitter_test"]:
			twitter.PostTweet(msg)
		elif sys.argv[1] == "test":
			funcs.printlog(msg)

	else: # unknown mode
		print "Unknown second argument."
		sys.exit(1)

if __name__ == '__main__':
	funcs.printpid()
	main()