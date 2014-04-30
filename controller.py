# Audio Playlist Resume (APR)
# Copyright (C) 2014 Timothy Hayes
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import xbmc
import json

class MusicPlayListState():
	def __init__(self, valid, playlist_idx = 0, file_offset = 0):
		self.valid = valid
		self.playlist_idx = playlist_idx
		self.file_offset = file_offset
	def __repr__(self):
		return "<MusicPlayListState@%d valid:%s, playlist_idx:%d, file_offset:%d>" % (id(self), self.valid, self.playlist_idx, self.file_offset)

# Class based on XBMC_JSON from 'XBMC Resume' by Matt Huisman
class JsonQuery:
    # Builds JSON request with provided json data
    def _buildRequest(self, method, params={}, jsonrpc='2.0', rid='1'):
        request = {'jsonrpc' : jsonrpc, 'method' : method, 'params' : params, 'id' : rid }
        return request
    
    # Performs single JSON query and returns result boolean, data dictionary and error string
    def _query(self, request):
        result = False
        data = {}
        error = ''
        
        if ( request ):
            response = self._execute(request)
            if ( response ):
                result = self._checkReponse(response)
                if ( result ):
                    data = response['result']
                else: error = response['error']
                
        return (result, data, error)
                    
    # Checks JSON response and returns boolean result
    def _checkReponse(self, response):
        result = False
        if ( ('result' in response) and ('error' not in response) ):
            result = True
        return result
    
    # Executes JSON request and returns the JSON response
    def _execute(self, request):
        request_string = json.dumps(request)
        response = xbmc.executeJSONRPC(request_string)  
        if ( response ):
            response = json.loads(response)
        return response

    # Execute a query without and simply returns boolean of success/failure.
    def executeNonQuery(self, method, params={}):
        request = self._buildRequest(method, params)
        result = self._query(request)[:1]
        return result
    
    # Executes a query and returns a single value. Default value can be returned if query fails.
    def executeScalar(self, method, params={}, default='', allowEmpty=True):
        value = default
        request = self._buildRequest(method, params)
        result, data = self._query(request)[:2]
        if ( result and data ):
            if isinstance(data, dict):
                data = data[data.keys()[0]]
            if ( allowEmpty or data ):
                value = data
        return value


class XbmcControl():
	def __init__(self):
		self._json = JsonQuery()
		self._player = xbmc.Player()
		self._musicplaylist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

	def getMusicPlaylistState(self):
		if (self._musicplaylist.size() > 0):
			playlist_idx = self._musicplaylist.getposition()
		else:
			xbmc.log("APR@ music playlist is empty", xbmc.LOGDEBUG)
			return MusicPlayListState(valid=False)
		try:
			file_offset = int(self._player.getTime())
		except:
			xbmc.log("APR@ could not get current time of running file", xbmc.LOGDEBUG)
			return MusicPlayListState(valid=False)
		return MusicPlayListState(True, playlist_idx, file_offset)

	def setMusicPlaylistState(self, playlist_state, reset_position):
		if not (playlist_state.valid):
			xbmc.log("APR@ music playlist state is not valid", xbmc.LOGDEBUG)
			return
		if not (self._json.executeNonQuery('Player.Open', {'item' : {'playlistid' : xbmc.PLAYLIST_MUSIC, 'position' : playlist_state.playlist_idx}})):
			xbmc.log("APR@ could not play item", xbmc.LOGDEBUG)
			return
		if (reset_position):
			xbmc.log("APR@ resetting file position", xbmc.LOGDEBUG)
			return
		m, s = divmod(playlist_state.file_offset, 60)
		h, m = divmod(m, 60)
		# there is a race condition between the file being played and being able to seek it
		xbmc.sleep(50)
		if not (self._json.executeNonQuery('Player.Seek', {'playerid' : xbmc.PLAYLIST_MUSIC, 'value' : {'hours' : int(h), 'minutes' : int(m), 'seconds' : int(s)}})):
			xbmc.log("APR@ could not go to position", xbmc.LOGDEBUG)
		return

	def getVolume(self):
		result = self._json.executeScalar('Application.GetProperties', {'properties' : ['volume']}, None)
		if (result is None):
			xbmc.log("APR@ could not retrieve volume", xbmc.LOGDEBUG)
			return None
		return int(result)

	def setVolume(self, volume):
		result = self._json.executeNonQuery('Application.SetVolume', {'volume' : volume})
		if not (result):
			xbmc.log("APR@ could not restore volume", xbmc.LOGDEBUG)
		return