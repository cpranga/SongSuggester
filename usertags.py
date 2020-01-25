'''
Purpose: find recommended songs for the user based on their topTracks of all time

Output:
'''

import requests
import json
from time import sleep
from os.path import exists

#default paramaters to be sent with every request to lastfm API
mainParams= {
	'format': 'json',
	'period': 'overall'
}

#functions are defined here

'''
createCredentials

Purpose: creates credentials file that contains username and api key
'''
def createCredentials():
	with open("credentials.txt", 'w') as outfile:
		username = input("Username: ")
		apikey = input("API Key: ")
		outfile.write(username + " " + apikey)
	print("Credentials created.")

'''
parseCredentials

Purpose: reads through a credetials file to load credentials (user id and api key) into the mainParams
'''
def parseCredentials():
	with open("credentials.txt", "r") as infile:
		line = infile.read().split()
		mainParams.update({
			'user': line[0],
			'api_key': line[1]
			})

'''
jrpint

Arg: obj -> requst data type
Purpose: prints out the requests JSON info to screen
'''
def jprint(obj):
	try:
		text = json.dumps(obj.json(), sort_keys=True, indent=4)
	except:
		text = json.dumps(obj, sort_keys=True, indent=4)
	print(text)

'''
getUserTopSongs

Purpose: queries the last.fm API to retrieve the users most listened to songs
'''
def getUserTopSongs():
	#change param variables
	tmpParams={
		'method' : "user.getTopTracks",
		'limit' : 30
	}
	request = makeRequest(tmpParams)
	writejson(request, "toptracks")

'''
requestErrorCheck

Purpose: checks the status_code of the request to determine if an error occured (status_code >= 400)
Args: request
'''
def requestErrorCheck(request):
	if request.status_code >= 400:
		print("Error thrown for API request. Exiting")
		print(str(request.status_code))
		exit(0)

'''
writejson

Purpose: writes the json of a request to two files
	- one file is made to be readable by a human
	- the other file will have json statements seperated by lines
Arguments:
	request:
		- either a single request
		- or a list of multiple requests
	method:
		- which method did the calling. Determines output file and datatype of request
'''
def writejson(request, method):
	'''
	Checks which method called
	- if method is toptracks
		- open up toptracks files, and print single request to both files
	- else if method is similarsongs
		- open up similar songs files
		- print each json, then print blankline to seperate
	'''
	if method == "toptracks":
		with open('toptracks.json', 'w') as outfile, open('toptracks_readable.json', 'w') as outfile_read:
			outtext= request.json()
			json.dump(outtext, outfile)
			json.dump(outtext, outfile_read, sort_keys=True, indent=4)
	elif method == "similarsongs":
		with open('sugtracks.json', 'w') as outfile, open('sugtracks_readable.json', 'w') as outfile_read:
			for ind in request:
				outtext= ind.json()
				json.dump(outtext, outfile)
				json.dump(outtext, outfile_read, sort_keys=True, indent=4)
				outfile.write('\n')
				outfile_read.write('\n')

'''
parseTopTracks

Purpose: parses the toptracks.json file and creates a set containing a tuple of song name and artist name
Returns: tuple set of (song name , artist name)
'''
def parseTopTracks():
	#data=""
	#ToDo: ask user which file to open
	with open("toptracks.json", "r") as infile:
		data= json.load(infile)
	#root is a list
	root = data["toptracks"]["track"]
	'''
	creates an empty set to store tuples in
	'''
	toptracks = set()
	#iterate over every track block in root list
	for track in root:
		#store information inside of set
		toptracks.add((track["name"], track["artist"]["name"]))
	return toptracks

'''
getSimilarSongs

Purpose: find similar songs for each track in the tracklist
Arguments:
	- tracklist: set of tuples (song name, artist)
Logic:
	- define necessary request paramaters
	- initialize empty containers
	- iterate over every track in tracklist
		- make request
		- append request to container
	- call writejson with suggested songs container
'''
def getSimilarSongs(tracklist):
	#initialize params dict with values that will not be changing
	tmpParams={
		'method' : 'track.getSimilar',
		'limit' : 30
	}

	'''
	iterate over every track
		update the mbid param field to current tracks mbid
		make request to last.fm
		print out request
		debugging: exit after single request
	'''
	requestsList= []
	sugTracks={}

	for line in tracklist:
		tmpParams['track'], tmpParams['artist'] = line
		request =makeRequest(tmpParams)
		requestsList.append(request)
	writejson(requestsList, "similarsongs")

'''
parseSimTracks

Purpose: parses the similartracks json file to prepare info to be presented
Logic:
	- call parseTopTracks() to return a container of the top tracks
		- we will be using this container to ensure we do not reccoment a song already in the top tracks
	- create a dict to keep track of suggested songs and frequency
		(track name, artist name) : frequency
	- open the suggested tracks json file
	- iterate over every line in the file. each line is a different json request info
		- iterate over every track in the line
			- find relevent information: track name and artist name
			- check if already in topTracks
			- increase count of track appearing in
				- or append it if not already present
	- return the suggested tracks dict
'''
def parseSimTracks():
	'''
	opens sugtracks.json
	- each line of file contains a different json string
	'''
	topTracks= parseTopTracks()
	sugTracks={}
	with open("sugtracks.json", "r") as infile:
		for line in infile:
			#serializes line into json format
			data = json.loads(line)
			#iterates through tree to interesing data
			root = data["similartracks"]["track"]

			#iterate over every suggested track
			for track in root:
				name=track["name"]
				artist=track["artist"]["name"]
				#check if the song is already in the users toptracks
				#if so, continue to next track
				if (name, artist) in topTracks:
					continue
				#try incrementing the count for the song
				try:
					sugTracks[(artist,name)]["count"] +=1
				#if it failed, it means it was not present
				#so add it in
				except:
					#try adding it in
					try:
						sugTracks[(artist,name)]={
							'artist': artist,
							'track': name,
							'count': 1
						}
					#if it fails, print out the info
					except:
						print("Exception encountered in parseSimTracks()")
						jprint(track)
						exit()
	return sugTracks

'''
getTopSongs

Purpose: parses through passed in dict containing suggested songs and sorts them in descending order, based on number of times each song was suggested
Arguments: source -> dict
	(artist name, track name): count, artist name, track name
'''
def getTopSongs(source):
	#creates a temp copy of the passed in dict
	tmpDict= source.copy()
	#used to store songs that have been suggested already
	topDict={}

	#opens output file called sugtracks.csv
	'''
	CSV format
	-first line is headers
	- following lines represent a suggested song
		-artist , track, and count of times suggested
	'''
	with open("sugtracks.csv", "w", encoding="utf-8") as outfile:
		#prints headers for csv file
		outfile.write("Artist, Track, Count" + '\n')
		while len(tmpDict) > len(topDict):
			max = -1
			maxIt = {}
			maxKey = ()
			maxItems={}
			for key, items in tmpDict.items():
				if key in topDict:
					continue
				if items["count"] > max:
					maxKey = key
					maxItems= items
					max = items["count"]
			topDict[maxKey] = maxItems
			artist, track = maxKey
			outfile.write(artist + ", " + track + ", " + str(max) + '\n')
			print(artist + ", " + track + ", " + str(max))

def makeRequest(params):
	#wait a quarter of a second
	sleep(.25)
	headers = {
		'user-agent' : 'Chasezx3'
	}

	'''
	Last.fm paramaters:
		user: username to look yp
		api_key: identifier for client
		method: what we want to do
		format: we want json returned
		period: time period to search over
		limit: set low number of values for debugging
	'''


	sendParams = {**params, **mainParams}
	#append params to params
	#params.update(params)
	request = requests.get('http://ws.audioscrobbler.com/2.0/', headers=headers, params=sendParams)
	requestErrorCheck(request)
	return request

#############################################################
#main code starts here

resp = input("Would you like to update the JSON files? y/n: ")
if resp.lower() == 'y':
	#check if credentyials file exists
	if exists('credentials.txt') == False:
		print("Credentials file not found. Starting process of creating credentials file.")
		createCredentials()
	parseCredentials()
	print("Making requests.")
	getUserTopSongs()

	topTracks = parseTopTracks()
	getSimilarSongs(topTracks)
	print("Requests completed.")

sugTracks = parseSimTracks()
#print(sugTracks)

getTopSongs(sugTracks)
