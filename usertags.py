'''
Purpose: find recommended songs for the user based on their topTracks of all time

Output:
'''

import requests
import json
from time import sleep

#default paramaters to be sent with every request to lastfm API
mainParams= {
	'format': 'json',
	'period': 'overall'
}

#functions are defined here

def parseCredentials():
	with open("credentials.txt", "r") as infile:
		line = infile.read().split()
		mainParams.update({
			'user': line[0],
			'api_key': line[1]
			})
	print(mainParams)

#prints out blanket of json info
def jprint(obj):
	try:
		text = json.dumps(obj.json(), sort_keys=True, indent=4)
	except:
		text = json.dumps(obj, sort_keys=True, indent=4)
	print(text)

def getUserTopSongs():
	#change param variables
	tmpParams={
		'method' : "user.getTopTracks",
		'limit' : 50
	}
	request = makeRequest(tmpParams)
	writejson(request)

def requestErrorCheck(request):
	if request.status_code >= 400:
		print("Error thrown for API request. Exiting")
		print(str(request.status_code))
		exit(0)

def writejson(request):
	with open('toptracks.json', 'w') as outfile:
		outtext= request.json()
		json.dump(outtext, outfile)
	with open('toptracks_readable.json', 'w') as outfile:
		outtext= request.json()
		json.dump(outtext, outfile, sort_keys=True, indent=4)
		#json.dumps(obj, sort_keys=True, indent=4)

def parseTopTracks():
	#data=""
	#ToDo: ask user which file to open
	with open("toptracks.json", "r") as infile:
		data= json.load(infile)
	#root is a list
	root = data["toptracks"]["track"]
	'''
	create a empty dict to store the users top tracks
	dict will store
		tracks name as the key
		tracks mbid (identifier) as the value
	'''
	toptracks = set()
	#iterate over every track block in root list
	for track in root:
		#store information inside of dict
		toptracks.add((track["name"], track["artist"]["name"]))
	return toptracks

def getSimilarSongs(tracklist):
	#initialize params dict with values that will not be changing
	tmpParams={
		'method' : 'track.getSimilar',
		'limit' : 20
	}

	'''
	iterate over every track
		update the mbid param field to current tracks mbid
		make request to last.fm
		print out request
		debugging: exit after single request
	'''

	sugTracks={}
	with open('sugtracks.json', 'w') as outfile:
		for line in tracklist:
			tmpParams['track'], tmpParams['artist'] = line
			#print(tmpParams['track'], tmpParams['artist'])
			#tmpParams['artist'] = artist
			#tmpParams['track'] = track
			request =makeRequest(tmpParams)

			#block of code writes out request for debugging purposes
			'''
			with open('sugtracks.json', 'w') as outfile:
				outtext= request.json()
				json.dump(outtext, outfile)
			with open('sugtracks_readable.json', 'w') as outfile:
				outtext= request.json()
				json.dump(outtext, outfile, sort_keys=True, indent=4)
				#json.dumps(obj, sort_keys=True, indent=4)
			jprint(request)
			'''
			outtext = request.json()
			json.dump(outtext, outfile)
			#json.dump(outtext, outfile_read, sort_keys=True, indent=4)
			outfile.write("\n")

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

def getTopSongs(source):
	tmpDict= source.copy()
	topDict={}
	with open("sugtracks.csv", "w", encoding="utf-8") as outfile:
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
		print(topDict)

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

parseCredentials()
#ask if user wants to make a new request to API
resp = input("Would you like to update the top tracks json file? y/n:  ")
if resp.lower() == 'y':
	print("Making request.")
	getUserTopSongs()
	print("Request completed.")

topTracks=parseTopTracks()
resp= input("Would you like to update the similar tracks json file? y/n:	")
if resp.lower() == 'y':
	print("Making request.")
	getSimilarSongs(topTracks)
	print("Request completed.")

sugTracks = parseSimTracks()
#print(sugTracks)

getTopSongs(sugTracks)
