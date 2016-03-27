'''
Created on Mar 25, 2016

@author: Chris
'''
import subprocess
import config
import database
import musicsyncer
import argparse

parser = None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Syncs youtube playlists with spotify automatically")
    parser.add_argument("--drop", help="Refreshes the DB", action='store_true')
    parser.add_argument("--addyoutube", help="Adds youtube playlist", default=None)
    parser.add_argument("--addspotify", help="Adds youtube playlist", default=None)
    parser.add_argument("--sync", help="Sync playlists", action='store_true')
    parser.add_argument("--download", help="Download new found songs", action='store_true')
    args = parser.parse_args()
    
    if args.drop:
        database.drop_database()
    if args.addyoutube:
        musicsyncer.add_youtube_playlist(args.addyoutube)
    if args.addspotify:
        spotify_id = args.addspotify.split(":")
        musicsyncer.add_spotify_playlist(spotify_id[2], spotify_id[4])
    if args.sync:
        for playlists in database.session.query(database.ConnectedPlaylist):
            print "Syncing %s" % playlists.name
            musicsyncer.sync_youtube_videos(playlists.youtube_playlist, playlists.spotify_playlist)
    if args.download:
        while musicsyncer.download_new_song() is True:
            pass