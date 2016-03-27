'''
Created on Mar 25, 2016

@author: Chris
'''
from sqlalchemy import create_engine, Column, Integer, String, Boolean, TIMESTAMP, func, Enum, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

class Source():
    youtube = 0
    spotify = 1

engine = create_engine('sqlite:///database.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


def drop_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)



class YoutubeSong(Base):
    __tablename__ = 'youtubesongs'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    youtube_id = Column(String)
    duration = Column(Integer)
    date_added = Column(TIMESTAMP, server_default=func.now())
    on_spotify = Column(Boolean, default=False)
    
    spotify_song_id = Column(Integer, ForeignKey("spotifysongs.id"))
    spotify_song = relationship("SpotifySong", foreign_keys=[spotify_song_id], post_update=True)
    
    youtube_playlist_id = Column(Integer, ForeignKey("youtubeplaylists.id"))
    youtube_playlist = relationship("YoutubePlaylist", foreign_keys=[youtube_playlist_id])
    
    download_id = Column(Integer, ForeignKey("downloads.id"))
    download = relationship("Download", foreign_keys=[download_id], post_update=True)
    
class SpotifySong(Base):
    __tablename__ = 'spotifysongs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist = Column(String)
    spotify_id = Column(String)
    duration = Column(Integer)
    date_added = Column(TIMESTAMP, server_default=func.now())
    on_youtube = Column(Boolean, default=False)
    
    youtube_song_id = Column(Integer, ForeignKey(YoutubeSong.id))
    youtube_song = relationship("YoutubeSong", foreign_keys=[youtube_song_id], post_update=True)
    
    spotify_playlist_id = Column(Integer, ForeignKey("spotifyplaylists.id"))
    spotify_playlist = relationship("SpotifyPlaylist", foreign_keys=[spotify_playlist_id])


class YoutubePlaylist(Base):
    __tablename__ = 'youtubeplaylists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    songcount = Column(Integer)
    youtube_id = Column(String)
    youtube_songs = relationship("YoutubeSong")
    connected_playlist = relationship("ConnectedPlaylist", uselist=False)
    
class SpotifyPlaylist(Base):
    __tablename__ = 'spotifyplaylists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    songcount = Column(Integer)
    spotify_id = Column(String)
    spotify_songs = relationship("SpotifySong")
    connected_playlist = relationship("ConnectedPlaylist", lazy="dynamic")
    
    
class ConnectedPlaylist(Base):
    __tablename__ = 'connectedplaylists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    source = Column(Integer)
    
    youtube_playlist_id = Column(Integer, ForeignKey(YoutubePlaylist.id))
    youtube_playlist = relationship("YoutubePlaylist", uselist=False, foreign_keys=[youtube_playlist_id])
    
    spotify_playlist_id = Column(Integer, ForeignKey(SpotifyPlaylist.id))
    spotify_playlist = relationship("SpotifyPlaylist", uselist=False, foreign_keys=[spotify_playlist_id])
    
    
class Download(Base):
    __tablename__ = 'downloads'
    id = Column(Integer, primary_key=True)
    completed = Column(Boolean, default=False)
    filename_restricted = Column(String)
    filename_renamed = Column(String)
    
    youtube_song_id = Column(Integer, ForeignKey(YoutubeSong.id))
    youtube_song = relationship("YoutubeSong", foreign_keys=[youtube_song_id], post_update=True)