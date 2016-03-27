from ConfigParser import SafeConfigParser
import os

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

parser = SafeConfigParser()
parser.read(os.path.join(CURRENT_PATH, 'config.ini'))

SPOTIPY_CLIENT_ID = parser.get('spotipy', 'client_id')
SPOTIPY_CLIENT_SECRET = parser.get('spotipy', 'client_secret')
SPOTIPY_REDIRECT_URI = parser.get('spotipy', 'redirect_uri')

SPOTIFY_USER = parser.get('spotify', 'user')
SPOTIFY_SCOPE = 'playlist-modify-public'

CLIENT_SECRETS_FILE = os.path.join(CURRENT_PATH, parser.get('youtube', 'secrets_file'))
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MUSIC_CACHE_LOCATION = parser.get('directory', 'cache_location')
MUSIC_FINISHED_DESTINATION = parser.get('directory', 'finished_destination')

YOUTUBE_DL_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        #'preferredquality': 'best',
        'preferredquality': '192',
    }],
}
