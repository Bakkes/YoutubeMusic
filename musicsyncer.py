'''
Created on Mar 25, 2016

@author: Chris
'''
from database import *
from config import *
from spotipy import util, Spotify

import youtube_dl
import httplib2
import re
import os
import eyed3
from subprocess import call
from main import parser
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow


__spotify = None
flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
  message="No client secrets",
  scope=YOUTUBE_READ_WRITE_SCOPE)

storage = Storage("%s-oauth2.json" % "stored")
credentials = storage.get()

if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, parser)

__youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
  http=credentials.authorize(httplib2.Http()))



def get_spotify():
    global __spotify
    if __spotify is None:
        spotify_token = util.prompt_for_user_token(SPOTIFY_USER, SPOTIFY_SCOPE, client_id=SPOTIPY_CLIENT_ID, 
                                                   client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)
        __spotify = Spotify(spotify_token)
    return __spotify

#spotify:user:ijtrippin:playlist:6DPXOqJ2UJ9geWgzBHPiRg
def add_spotify_playlist(owner, playlist_id):
    spotify = get_spotify()
    spotify_playlist = spotify.user_playlist(owner, playlist_id)
    playlists_query = session.query(ConnectedPlaylist).filter(ConnectedPlaylist.spotify_playlist.has(spotify_id=playlist_id))
    if playlists_query.count() == 0:
        con_playlist = ConnectedPlaylist()
        con_playlist.source = Source.spotify
        con_playlist.name = spotify_playlist["name"]
        
        
        db_spotify_playlist = SpotifyPlaylist()
        db_spotify_playlist.name = spotify_playlist["name"]
        db_spotify_playlist.spotify_id = spotify_playlist["id"]
        
        db_youtube_playlist = YoutubePlaylist()
        db_youtube_playlist.name = spotify_playlist["name"]
        db_youtube_playlist.youtube_id = create_youtube_playlist(spotify_playlist["name"])
        
        con_playlist.spotify_playlist = db_spotify_playlist
        con_playlist.youtube_playlist = db_youtube_playlist
        #db_spotify_playlist
        session.add(con_playlist)
        
        
    else:
        return False #already exists
    
    
    session.commit()
    
def add_youtube_playlist(playlist_id):
    yt = __youtube
    playlist_feed_search = yt.playlists().list(part="snippet", id=playlist_id).execute()
    
    if len(playlist_feed_search["items"]) == 0:
        return False
    
    playlist_feed = playlist_feed_search["items"][0]["snippet"]
    
    playlist_query = session.query(ConnectedPlaylist).filter(ConnectedPlaylist.youtube_playlist.has(youtube_id=playlist_id))
    if playlist_query.count() == 0:
        con_playlist = ConnectedPlaylist()
        con_playlist.source = Source.youtube
        con_playlist.name = playlist_feed["title"]
        
        db_youtube_playlist = YoutubePlaylist()
        db_youtube_playlist.name = playlist_feed["title"]
        db_youtube_playlist.youtube_id = playlist_id
        
        db_spotify_playlist = SpotifyPlaylist()
        db_spotify_playlist.name = playlist_feed["title"]
        db_spotify_playlist.spotify_id = create_spotify_playlist(playlist_feed["title"])
        
        con_playlist.youtube_playlist = db_youtube_playlist
        con_playlist.spotify_playlist = db_spotify_playlist
        session.add(con_playlist)
    
    session.commit()
    
    
def cheapen_name(name, stage):
    if stage == 0:
        return name
    if stage == 1:
        return re.sub('\(.*?\)','', cheapen_name(name, stage - 1))
    if stage == 2:
        return re.sub('\[.*?\]','', cheapen_name(name, stage - 1))
    if stage == 3:
        if "ft" in name:
            new_name = cheapen_name(name, stage - 1)
            return new_name[0:new_name.find("ft")] #ex: Dr. Dre - Still D.R.E. ft. Snoop Dogg

    return None
#type YoutubePlaylist
def sync_youtube_videos(yt_playlist, sp_playlist):
    spotify = get_spotify()
    res = __youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=yt_playlist.youtube_id,
        maxResults="50"
    ).execute()
    if(res["pageInfo"]["totalResults"] != yt_playlist.songcount):
        print "Found some new ones"
        nextPageToken = res.get('nextPageToken')
        print res
        while ('nextPageToken' in res):
            nextPage = __youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=yt_playlist.youtube_id,
            maxResults="50",
            pageToken=nextPageToken
            ).execute()
            res['items'] = res['items'] + nextPage['items']
    
            if 'nextPageToken' not in nextPage:
                res.pop('nextPageToken', None)
            else:
                nextPageToken = nextPage['nextPageToken']
            print "next youtube page"
        
        for item in res['items']:
            item_exists = session.query(YoutubeSong).filter_by(youtube_id=item["contentDetails"]["videoId"])
            if(item_exists.count() > 0):
                continue
            #print "NEW ITEM TO CHECK %s" % item["snippet"]["title"]
            yt_song = YoutubeSong()
            
            #print item
            yt_song.youtube_id = item["contentDetails"]["videoId"]
            yt_song.duration = 1#item["contentDetails"]["endAt"]
            yt_song.title = item["snippet"]["title"]
            yt_song = create_download_request(yt_song)
            
            searched_name = item["snippet"]["title"]
            best_result = None
            name_stage = 0
            while best_result == None and searched_name is not None:
                searched_name = cheapen_name(item["snippet"]["title"], name_stage)
                if searched_name is None:
                    continue
                spotify_results = spotify.search(q=searched_name)
                
                if(len(spotify_results["tracks"]["items"]) != 0):
                    #print "Found %i results for %s" % (len(spotify_results["tracks"]["items"]), searched_name)
                    best_result = spotify_results["tracks"]["items"][0]
                #else:
                    
                    #print "No result for %s" % searched_name
                name_stage = name_stage + 1
                
            #else: #save for another time
                #for i, t in enumerate(spotify_results['tracks']['items']):
                
            yt_song.youtube_playlist = yt_playlist
            if best_result is None:
                yt_song.on_spotify = False
            else:
                spotify_song = SpotifySong()
                spotify_song.spotify_id = best_result["id"]
                spotify_song.title = best_result['name']
                spotify_song.artist = best_result['artists'][0]["name"]
                spotify_song.duration = int(best_result["duration_ms"]) / 1000
                spotify_song.on_youtube = True
                spotify_song.youtube_song = yt_song
                yt_song.on_spotify = True
                yt_song.spotify_song = spotify_song
                spotify_song.spotify_playlist = sp_playlist
                spotify.user_playlist_add_tracks(SPOTIFY_USER, sp_playlist.spotify_id, {"spotify:track:%s" % best_result["id"]})
                
            session.add(yt_song)
        session.add(yt_playlist)
        yt_playlist.songcount = res["pageInfo"]["totalResults"]
        session.commit()
    
    spotify_list = spotify.user_playlist(SPOTIFY_USER, sp_playlist.spotify_id)
    if sp_playlist.songcount == len(spotify_list["tracks"]["items"]):
        print "No change in song length"
        return
    for item in spotify_list["tracks"]["items"]:
        found_youtube = session.query(SpotifySong).filter_by(spotify_id=item["track"]["id"])
        if found_youtube.count() > 0:
            continue
        
        spot_song = SpotifySong()
        spot_song.artist = item["track"]["artists"][0]["name"]
        spot_song.title = item["track"]["name"]
        spot_song.spotify_id = item["track"]["id"]
        spot_song.duration = int(item["track"]["duration_ms"]) / 1000
        spot_song.spotify_playlist = sp_playlist
        extra = "EXPLICIT" if item["track"]["explicit"] else ""
        yt_search_result = __youtube.search().list(
            part="snippet",
            q = "%s %s %s" % (spot_song.artist, spot_song.title, extra),
            type = "video"
        ).execute()
        
        
        if(yt_search_result["pageInfo"]["totalResults"] == 0):
            spotify_song.on_youtube = False
        else:
            
            best_result = yt_search_result["items"][0]
            if "video" in best_result and "video" not in yt_search_result["items"][1]:
                best_result = yt_search_result["items"][1]
                
            yt_song = YoutubeSong()
            yt_song.title = best_result["snippet"]["title"]
            yt_song.youtube_id = best_result["id"]["videoId"]
            yt_song.duration = 1
            yt_song.on_spotify = True
            yt_song.spotify_song = spot_song
            yt_song.youtube_playlist = yt_playlist
            yt_song = create_download_request(yt_song)
            spot_song.on_youtube = True
            spot_song.youtube_song = yt_song
            execres = __youtube.playlistItems().insert(part="snippet", body={"snippet": {
                                                                                         "playlistId": yt_playlist.youtube_id,
                                                                                         "resourceId":
                                                                                            {
                                                                                             'kind': 'youtube#video', 
                                                                                             "videoId": yt_song.youtube_id}
                                                                                             }
                                                                             }).execute()
            session.add(spot_song)
    sp_playlist.songcount = len(spotify_list["tracks"]["items"])
    session.add(sp_playlist)       
    session.commit()
      
def create_download_request(yt_song):
    dl_request = Download()
    dl_request.youtube_song = yt_song
    yt_song.download = dl_request
    return yt_song
      
def create_spotify_playlist(name):
    sp = get_spotify()
    created_playlist = sp.user_playlist_create(SPOTIFY_USER, name, True)
    print "Created spotify playlist %s" % name
    return created_playlist["id"]

def create_youtube_playlist(name):
    insert_response = __youtube.playlists().insert(
                                 part="snippet,status",
                                 body=dict(
                                           snippet=dict(
                                                        title=name,
                                                        description="Automatically synced with spotify playlist %s" % name
                                                        )
                                           )
                                 ).execute()
    return insert_response["id"]


def download_new_song():
    queued_download = session.query(Download).filter_by(completed=False).first()
    if queued_download is None:
        return False
    filename = "unicode(%(title)s).%(ext)s"

    #
    spot_song = None
    if queued_download.youtube_song.on_spotify:
        spot_song = queued_download.youtube_song.spotify_song
        filename = "%s - %s.%s" % (spot_song.artist, spot_song.title, "%(ext)s")
    
    playlist_name = queued_download.youtube_song.youtube_playlist.connected_playlist.name
    YOUTUBE_DL_OPTIONS['outtmpl'] = "%s/%s" % (MUSIC_CACHE_LOCATION, filename)
    
    with youtube_dl.YoutubeDL(YOUTUBE_DL_OPTIONS) as ydl:
        res = ydl.download(["http://www.youtube.com/watch?v=%s" % queued_download.youtube_song.youtube_id], )
        mp3file = os.listdir(MUSIC_CACHE_LOCATION)[0]
        mp3file_name = mp3file[mp3file.rfind("/") + 1:]
        if queued_download.youtube_song.on_spotify:
            tag = eyed3.load("%s/%s" % (MUSIC_CACHE_LOCATION, mp3file))
            tag.tag.title = spot_song.title
            tag.tag.artist = spot_song.artist
            tag.tag.artist_url = queued_download.youtube_song.youtube_id
            tag.tag.save(version=(1,None,None))
            
        dest_dir = "%s/%s" % (MUSIC_FINISHED_DESTINATION, playlist_name)
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
        dest_file = "%s/%s" % (dest_dir, mp3file_name)
        os.rename("%s/%s" % (MUSIC_CACHE_LOCATION, mp3file), dest_file)
    queued_download.completed = True
    session.add(queued_download)
    session.commit()
    
    return True
        