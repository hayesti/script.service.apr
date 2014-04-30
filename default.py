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
import xbmcaddon
import controller

class PlayerWithRestore(xbmc.Player):
	def __init__(self, restore_volume=True, reset_track=False, notify_on_resume=True, icon=None):
		self._setting_restore_volume = restore_volume
		self._setting_reset_track = reset_track
		self._notify_on_resume = notify_on_resume
		self._icon = icon
		self._started_music_playlist = False
		self._resume_music_playlist = False
		self._volume_to_restore = 0
		self._controller = controller.XbmcControl()
		self._music_playlist_state = controller.MusicPlayListState(valid=False)

	def updateMusicPlaylistState(self):
		self._music_playlist_state = self._controller.getMusicPlaylistState()
		xbmc.log("APR@ music playlist state updated: %s" % self._music_playlist_state, xbmc.LOGDEBUG)

	def onPlayBackStarted(self):
		if (self.isPlayingVideo() and self._started_music_playlist):
 			# we will want to resume our audio playlist after
			self._resume_music_playlist = True
			xbmc.log("APR@ video interrupted audio playlist", xbmc.LOGDEBUG)
			# measure volume
			self._volume_to_restore = self._controller.getVolume()
			xbmc.log("APR@ volume was %d when video started" % self._volume_to_restore, xbmc.LOGDEBUG)
		self._started_music_playlist = self.isPlayingAudio()

	def onPlayBackStopped(self):
		self._started_music_playlist = False
		if (self._resume_music_playlist):
			xbmc.log("APR@ attempt to resume audio playlist", xbmc.LOGDEBUG)
			self._resume_music_playlist = False
			# pause for a second 
			xbmc.sleep(1000)
			# restore volume
			if (self._setting_restore_volume):
				self._controller.setVolume(self._volume_to_restore)
				xbmc.log("APR@ restored volume to %d" % self._volume_to_restore, xbmc.LOGDEBUG)
			# resume playing the file
			if not (self._music_playlist_state.valid):
				xbmc.log("APR@ music playlist state is not valid", xbmc.LOGDEBUG)
				return
			self._controller.setMusicPlaylistState(self._music_playlist_state, self._setting_reset_track)
			xbmc.log("APR@ restored playlist to %s" % self._music_playlist_state, xbmc.LOGDEBUG)
			# make a popup notification
			if (self._notify_on_resume):
				xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%("Audio Playlist Resume", "Resuming audio playlist", 5000, self._icon))
		else:
			xbmc.log("APR@ not necessary to resume audio playlist", xbmc.LOGDEBUG)

	def onPlayBackEnded(self):
		self.onPlayBackStopped()

if (__name__ == '__main__'):
	xbmc.log("APR@ Audio Playlist Resume service: starting", xbmc.LOGNOTICE)
	 
	addon       = xbmcaddon.Addon(id='script.service.apr')
	addonname   = addon.getAddonInfo('name')
	version		= addon.getAddonInfo('version')

	xbmc.log("APR@ Audio Playlist Resume version %s" % version, xbmc.LOGNOTICE)

	s_restore_volume	= addon.getSetting("restore_volume").lower() == "true"
	s_reset_track 		= addon.getSetting("reset_track").lower() == "true"
	s_notify_on_resume 	= addon.getSetting("notify_on_resume").lower() == "true"
	xbmc.log("APR@ setting: restore_volume=%s" % s_restore_volume, xbmc.LOGDEBUG)
	xbmc.log("APR@ setting: reset_track=%s" % s_reset_track, xbmc.LOGDEBUG)
	xbmc.log("APR@ setting: notify_on_resume=%s" % s_notify_on_resume, xbmc.LOGDEBUG)

	icon = addon.getAddonInfo('icon')
	xbmc.log("APR@ icon=%s" % icon, xbmc.LOGDEBUG)

	player = PlayerWithRestore(restore_volume=s_restore_volume, reset_track=s_reset_track, notify_on_resume=s_notify_on_resume, icon=icon)

	while (not xbmc.abortRequested):
		xbmc.sleep(5000)

		if (player.isPlayingAudio()):
			player.updateMusicPlaylistState()

	xbmc.log("APR@ Audio Playlist Resume service: stopping", xbmc.LOGNOTICE)