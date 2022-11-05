import requests
import os
import spotipy
import json
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

token = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
cache_token = token.get_access_token()
sp = spotipy.Spotify(cache_token)


genre_response = requests.get('https://api.spotify.com/v1/recommendations/available-genre-seeds', headers=headers)
genres = genre_response.json()["genres"]

removed_genres = ['alt-rock', 'ambient', 'anime', 'black-metal', 'bluegrass', 'bossanova',
'brazil', 'breakbeat', 'british', 'chicago-house', 'children', 'comedy', 'dancehall',
'death-metal', 'deep-house', 'detroit-techno', 'dub', 'electro', 'electronic', 'emo', 
'forro', 'french', 'funk', 'garage', 'german', 'grindcore', 'groove', 'grunge', 'hard-rock', 
'hardcore', 'hardstyle', 'honky-tonk', 'house', 'idm', 'indian', 'indie-pop', 'industrial', 
'iranian', 'j-dance', 'j-idol', 'j-rock', 'kids', 'malay', 'metal-misc', 'metalcore', 
'minimal-techno', 'mpb', 'new-age', 'new-release', 'pagode', 'party', 'philippines-opm', 
'pop-film', 'post-dubstep', 'power-pop', 'progressive-house', 'psych-rock', 'punk-rock', 
'road-trip', 'rockabilly', 'sertanejo', 'show-tunes', 'singer-songwriter', 'songwriter', 
'spanish', 'summer', 'swedish', 'synth-pop', 'tango', 'techno', 'trance', 'trip-hop', 
'turkish', 'work-out', 'world-music']

for genre in removed_genres:
    genres.remove(genre)

tracks_by_genre = {}
for genre in genres:
    search_response1 = requests.get('https://api.spotify.com/v1/search?q=genre%%3A%s&type=track&market=US&limit=50' % genre, headers=headers)
    search_response2 = requests.get('https://api.spotify.com/v1/search?q=genre%%3A%s&type=track&market=US&limit=50&offset=51' % genre, headers=headers)

    if len(search_response1.json()["tracks"]["items"]) < 50 or len(search_response2.json()["tracks"]["items"]) < 50:
            continue
    
    tracks_by_genre[genre] = []
    unwanted_vars = ["type", "id", "uri", "analysis_url", "track_href"]
    
    for i in range(50):
        track_name = search_response1.json()["tracks"]["items"][i]["name"]
        track_url = search_response1.json()["tracks"]["items"][i]["external_urls"]["spotify"]
        
        audio_features = sp.audio_features(track_url[track_url.rindex("/")+1:])
        for j in range(len(unwanted_vars)):
            audio_features[0].pop(unwanted_vars[j])
        tracks_by_genre[genre].append({track_name: audio_features})

    for i in range(50):
        track_name = search_response2.json()["tracks"]["items"][i]["name"]
        track_url = search_response2.json()["tracks"]["items"][i]["external_urls"]["spotify"]

        audio_features = sp.audio_features(track_url[track_url.rindex("/")+1:])
        for j in range(len(unwanted_vars)):
            audio_features[0].pop(unwanted_vars[j])
        tracks_by_genre[genre].append({track_name: audio_features})

track_data = json.dumps(tracks_by_genre, indent=4)
with open("songsbygenre.json", "w") as outfile:
    outfile.write(track_data)   


top100_songs = {}
for i in range(2000, 2001): #1946-2021
    top100_songs[i] = []
    stream = os.popen("wget -qO- 'https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_%s' | grep -A 1 '<td>\"<a href=\"/wiki/'" % i)
    while True:
        song_name_line = stream.readline()
        if not song_name_line:
            break

        artist_name_line = stream.readline()
        stream.readline()

        song_name_line = song_name_line.replace('<', '>')
        song_split = song_name_line.split('>')
        song_name = song_split[4]

        artist_name_line = artist_name_line.replace('<', '>')
        artist_split = artist_name_line.split('>')
        artist_name = artist_split[4]

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

        if len(search_response.json()["tracks"]["items"]) == 0:
            warn("Song not found: %s by %s" % song_name, artist_name)
            continue

        track_name = search_response.json()["tracks"]["items"][0]["name"]
        track_url = search_response.json()["tracks"]["items"][0]["external_urls"]["spotify"]
        top100_songs[i].append((track_name, track_url))

# print(tracks_by_genre)
# print()
# print(len(tracks_by_genre))
# print()
# print(tracks_by_genre.keys())
# print()
# print(top100_songs)
# print()
# print(len(top100_songs))
# print()
# print(top100_songs.keys())





