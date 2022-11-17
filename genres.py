import requests
import json
import os
import re
from warnings import warn
 
AUTH_URL = 'https://accounts.spotify.com/api/token'
CLIENT_ID = "cada1a6f03b84727b0e5c59c973bd5a1"
CLIENT_SECRET = "25d8778fe7ea435fb964260e80bf6214"
 
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})
 
auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']
 
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}
 
genre_response = requests.get('https://api.spotify.com/v1/recommendations/available-genre-seeds', headers=headers)
genres = genre_response.json()["genres"]
 
tracks_by_genre = {}
for genre in genres[:3]:
    search_response1 = requests.get('https://api.spotify.com/v1/search?q=genre%%3A%s&type=track&market=US&limit=50' % genre, headers=headers)
    search_response2 = requests.get('https://api.spotify.com/v1/search?q=genre%%3A%s&type=track&market=US&limit=50&offset=51' % genre, headers=headers)
 
    if len(search_response1.json()["tracks"]["items"]) < 50 or len(search_response2.json()["tracks"]["items"]) < 50:
            continue
 
    tracks_by_genre[genre] = []
 
    for i in range(50):
        track_name = search_response1.json()["tracks"]["items"][i]["name"]
        track_url = search_response1.json()["tracks"]["items"][i]["external_urls"]["spotify"]
 
        tracks_by_genre[genre].append((track_name, track_url))
 
    for i in range(50):
        track_name = search_response2.json()["tracks"]["items"][i]["name"]
        track_url = search_response2.json()["tracks"]["items"][i]["external_urls"]["spotify"]
 
        tracks_by_genre[genre].append((track_name, track_url))
 
# parse top 100 hits from Wikipedia Billboard Year End Top Hits
top100_songs = {}
count = 1
for i in range(1966, 1972): #1946-2021
    top100_songs[i] = []
    #grep -A 1 '<td>\"<a href=\"/wiki/'
    #wget -qO- 'https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_1946' | grep -A 1 '<tr>'
    stream = os.popen("wget -qO- 'https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_%s' | grep -A 1 '<td>'" % i)
    #stream = os.popen("wget -qO- 'https://en.wikipedia.org/wiki/Billboard_year-end_top_30_singles_of_%s' | grep -A 1 '<td>'" % i)
    while True:
        first_line = stream.readline()
        if "<td>\"" in first_line:
            song_name_line = first_line
        else:
            song_name_line = stream.readline()
        # print(str(count) + 'song name' + song_name_line)
        if not song_name_line:
            break
 
        artist_name_line = stream.readline()
        stream.readline()
        # print('artist name' + artist_name_line)
 
        song_name_line = song_name_line.replace('<', '>')
        song_split = song_name_line.split('>')
        # for songs with no link
        if len(song_split) == 5:
            song_name = song_split[2]
        # for songs with links
        else: 
            song_name = song_split[4]
        # print('SONG SPLIT')
        # print(song_split)
        # print()
        # print('SONG NAME' + song_name)
 
        artist_name_line = artist_name_line.replace('<', '>')
        artists = re.split(' featuring | and | or | with ', artist_name_line)
        # print('ARTISTS ARR')
        # print(artists)
        artist_name = ''
        try:
            for artist in artists:
                artist_split = artist.split('>')
                if len(artist_split) == 1:
                    if (artist_name != ''):
                        artist_name += ', '
                    artist_name += artist_split[0]
                # for artists with no link
                elif len(artist_split) <= 5:
                    if (artist_name != ''):
                        artist_name += ', '
                    artist_name += artist_split[2]
                # for artists with links
                else:
                    if (artist_name != ''):
                        artist_name += ', '
                    artist_name += artist_split[4]
        except: 
            print('artist parsing failed')
        
        # print()
        # print('ARTIST NAME' + artist_name)

        song_name_line = stream.readline()
        # count += 1
 
        # find songs on spotify
        request_string = 'https://api.spotify.com/v1/search?query=track%3A'
 
        song_words = song_name.split()
        for j in range(len(song_words)):
            if j:
                request_string += '+'
 
            request_string += song_words[j]
 
        request_string += '+artist%3A'
 
        artist_words = artist_name.split()
        for j in range(len(artist_words)):
            if j:
                request_string += '%20'
 
            request_string += artist_words[j]
 
        request_string += '&type=track&market=US&locale=en-US%2Cen%3Bq%3D0.9%2Cja%3Bq%3D0.8%2Czh-CN%3Bq%3D0.7%2Czh%3Bq%3D0.6&offset=0&limit=1'
 
        search_response = requests.get(request_string, headers=headers)
        
        #warn("Song not found on Spotify: %s" % request_string)
        # if len(search_response.json()["tracks"]["items"]) == 0:
        #     continue
        if "tracks" not in search_response.json() or "items" not in search_response.json()["tracks"] or len(search_response.json()["tracks"]["items"]) == 0:
            continue
 
        track_name = search_response.json()["tracks"]["items"][0]["name"]
        track_url = search_response.json()["tracks"]["items"][0]["external_urls"]["spotify"]
        if (track_name, track_url) in top100_songs[i]:
            continue
        else: 
            top100_songs[i].append((track_name, track_url))
            
# print(tracks_by_genre)
# print()
# print(len(tracks_by_genre))
# print()
# print(tracks_by_genre.keys())
# print()
# print(top100_songs)
# print()
# print(len(top100_songs[1966]))
# print(len(top100_songs[1967]))
# print(len(top100_songs[1968]))
# print(len(top100_songs[1969]))
# print(len(top100_songs[1970]))
# print(len(top100_songs[1971]))
# print(len(top100_songs[1972]))
# print(len(top100_songs[1973]))
# print(len(top100_songs[1974]))
# print(len(top100_songs[1975]))
# print()
# print(len(top100_songs))
# print()
# print(top100_songs.keys())

# output = open("tophits.json", "w")
# json.dump(top100_songs, output, indent=4)
# output.close()

# # 1. Read file contents
# with open("tophits.json", "r") as file:
#     data = json.load(file)
# # 2. Update json object
# # data[1949] = top100_songs[1949]
# # 3. Write json file
# with open("tophits.json", "w") as file:
#     json.dump(data, file, indent=4)