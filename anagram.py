#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib
import logging
import sys
import json

class Config(object): # Configuration class
	def __init__(self):
		try:
			with open('./config.json') as file: # Load config.json
				config = json.loads(file.read())
		except IOError:
			sys.exit("Failed to open config file './config.json', are you sure it exists?".format(dictionaryPath))
		self.config = config

	def get(self, configName):
		return self.config[configName]
Config = Config() # Assign as global variable so accessible anywhere

def cleanWord(inputWord): # Sanitize word of special characters, etc.
	inputWord = inputWord.lower()
	validChars = list('abcdefghijklmnopqrstuvwxyz0123456789')
	outputWord = ''
	for letter in inputWord:
		if letter in validChars:
			outputWord += letter
	return outputWord

class Node(object):
	def __init__(self, letter = '', depth = 0, isFinal = False):
		self.letter   = letter  # Letter of the node
		self.depth	= depth   # Node depth
		self.isFinal  = isFinal # Whether it's a word or not
		self.children = {}	  # Node children

	def addWord(self, word): # Generate a new node tree from an input word
		node = self
		for index, letter in enumerate(word):
			if letter not in node.children: # If letter doesn't exist in tree, add it
				node.children[letter] = Node(letter =  letter,
											 depth  =  index + 1,
											 isFinal = index == len(word) - 1)
			node = node.children[letter]

	def generateAnagrams(self, chkWord): # Start going through the trie and generate new phrases
		letters = {}
		for letter in chkWord:
			letters[letter] = letters.get(letter, 0) + 1
		return self.next(self, letters, [], len(chkWord))

	def next(self, root, letters, path, minLength):
		if self.isFinal and self.depth >= Config.get('minimum_word_length'): # If it's a valid word & reaches the minimum word requirement
			word = ''.join(path) # Add it to the pile
			length = len(cleanWord(word))
			if length >= minLength:
				yield word
			path.append(' ') # Add space in-between letters
			for word in root.next(root, letters, path, minLength):
				yield word
			path.pop()

		for letter, node in self.children.items(): # Going down the tree...
			count = letters.get(letter, 0)
			if count == 0:
				continue
			letters[letter] = count - 1
			path.append(letter)
			for word in node.next(root, letters, path, minLength):
				yield word
			path.pop()
			letters[letter] = count

class Dictionary(object):
	def __init__(self, dictionaryPath):
		dictTrie  = Node() # Trie for generating new anagram phrases from separate words
		try:
			with open(dictionaryPath) as dictFile: # Create array of valid words
				for word in dictFile:
					dictTrie.addWord(cleanWord(word)) # Trie needs to be clean for best results
		except IOError:
			sys.exit("Failed to open dictionary '{0}', are you sure the path is correct?".format(dictionaryPath))

		self.dictTrie = dictTrie

	def generateAnagrams(self, chkWord): # Generate anagram with two words
		results = []
		for anagram in self.dictTrie.generateAnagrams(chkWord):
			results.append(anagram)
		return results

if __name__ == '__main__':
	dictionary = Dictionary(Config.get('dictionary_txt'))

class ServerHandler(BaseHTTPRequestHandler):
	def setResponse(self, type): # Sets the response header
		if (type == "ok"): # 200 OK (Successful)
			self.send_response(200)
			self.send_header('Content-type', 'text/json')
		elif (type == "bad"): # 400 BAD REQUEST (Malformed URL, etc.)
			self.send_response(400)
			self.send_header('Content-type', 'text/plain')
		elif (type == "notexist"): # 404 NOT FOUND (Malformed URL, etc)
			self.send_response(404)
			self.send_header('Content-type', 'text/plain')
		elif (type == "teapot"): # 418 I'M A TEAPOT (lol)
			self.send_response(418)
			self.send_header('Content-type', 'text/liar')
		self.end_headers()

	def do_GET(self):
		parsedGET = urllib.parse.parse_qs(self.path) # Parse GET query (e.g. ?q=query&id=000)
		parsedURL = urllib.parse.urlparse(self.path).path # Parse directory (e.g. /index.html)
		if (parsedURL == '/anagram'):
			try:
				chkWord = parsedGET['/anagram?q'][0] # Retrieve input query
				if (len(chkWord) <= Config.get('max_allowed_word_length')):
					self.setResponse('ok')
					anagrams = dictionary.generateAnagrams(chkWord) # Generate anagram and send it over
					self.wfile.write(json.dumps(anagrams).encode('utf-8'))
				else:
					raise
			except:
				self.setResponse('bad')
				self.wfile.write("400 Bad Request".encode('utf-8')) # Bad request (e.g. when missing GET query)
		else:
			self.setResponse('notexist') # Not found if anything other than http://ip:port/anagram
			self.wfile.write("404 Not Found".encode('utf-8'))
		return

def run(server_class=HTTPServer, handler_class=ServerHandler, address='', port=8080):
	logging.basicConfig(level=logging.INFO)
	server_address = (address, port)
	httpd = server_class(server_address, handler_class)
	logging.info('Starting server on {0}:{1}!\n'.format(address, str(port)))
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	logging.info('Stopping server!\n')

if __name__ == '__main__':
	run(address = Config.get('listen_address'),
		port    = Config.get('listen_port'))