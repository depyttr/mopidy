from __future__ import absolute_import, unicode_literals

import logging

import math

import pykka

from mopidy import mixer


logger = logging.getLogger(__name__)


class SoftwareMixer(pykka.ThreadingActor, mixer.Mixer):

    name = 'software'

    def __init__(self, config):
        super(SoftwareMixer, self).__init__(config)

        self.config = config
        self.volume_scale = self.config['softwaremixer']['volume_scale']

        self._audio_mixer = None
        self._initial_volume = None
        self._initial_mute = None
        self._volume = None

    def setup(self, mixer_ref):
        self._audio_mixer = mixer_ref

        # The Mopidy startup procedure will set the initial volume of a
        # mixer, but this happens before the audio actor's mixer is injected
        # into the software mixer actor and has no effect. Thus, we need to set
        # the initial volume again.
        if self._initial_volume is not None:
            self.set_volume(self._initial_volume)
        if self._initial_mute is not None:
            self.set_mute(self._initial_mute)

    def teardown(self):
        self._audio_mixer = None

    def get_volume(self):
        if self._audio_mixer is None:
            return None
        return self._volume

    def trigger_volume_changed(self, volume):
        super(SoftwareMixer, self).trigger_volume_changed(self._volume)

    def set_volume(self, volume):
        if self._audio_mixer is None:
            self._initial_volume = volume
            return False
        self._volume = volume
        self._audio_mixer.set_volume(self._mixer_to_volume(volume))
        return True

    def get_mute(self):
        if self._audio_mixer is None:
            return None
        return self._audio_mixer.get_mute().get()

    def set_mute(self, mute):
        if self._audio_mixer is None:
            self._initial_mute = mute
            return False
        self._audio_mixer.set_mute(mute)
        return True

    def _mixer_to_volume(self, mixer_volume):
        volume = mixer_volume
        if self.volume_scale == 'cubic':
            volume = volume * volume / 100.0
        elif self.volume_scale == 'log':
            volume = math.pow(10, volume / 50.0)
        return int(volume)
