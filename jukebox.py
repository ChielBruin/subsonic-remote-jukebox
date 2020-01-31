import vlc

class JukeboxStatus (object):
    def __init__(self, playing, time, index, gain):
        self.playing = playing
        self.time = time
        self.index = index
        self.gain = gain

    def to_json(self):
        format = b'''{
            "subsonic-response" : {
                "status" : "ok",
                "version" : "1.16.1",
                "jukeboxStatus" : {
                    "currentIndex" : %d,
                    "playing" : %s,
                    "gain" : %1.2f, 
                    "position":%d
                }
            }
        }'''
        playing = b'true' if self.playing else b'false'
        return format % (self.index, playing, self.gain, self.time)
    
    def to_xml(self):
        format_str = b'''<subsonic-response status="ok" version="1.16.1">
            <jukeboxStatus currentIndex="%d" playing="%s" gain="%1.2f" position="%d"/> 
        </subsonic-response>'''
        playing = b'true' if self.playing else b'false'
        return format_str % (self.index, playing, self.gain, self.time)

    
class Jukebox (object):
    def __init__(self, target):
        self.target = target
        self.instance = vlc.Instance()
        
        self.medialist = vlc.MediaList()
        self.player = vlc.MediaListPlayer(self.instance)
        self.player.set_media_player(self.instance.media_player_new())
        self.player.set_media_list(self.medialist)

        self.mrl_map = {}

    def get_status(self):
        return JukeboxStatus(
                    self.is_playing(), 
                    self.get_position(), 
                    self.get_index(), 
                    self.get_volume()
        )
    
    def get_playlist(self):
        return list(self.mrl_map.values())
    
    def set(self, id, credentials):
        self.mrl_map = {}
        media = self._build_media(id, credentials)
        
        # Create new list
        self.medialist = vlc.MediaList()
        self.player.stop()
        self.player.set_media_list(self.medialist)

        self.medialist.lock()
        for media_item in media:
            self.medialist.add_media(media_item)
        self.medialist.unlock()

    def add(self, id, credentials):
        media = self._build_media(id, credentials)

        self.medialist.lock()
        for media_item in media:
            self.medialist.add_media(media_item)
        self.medialist.unlock()

    def remove(self, index):
        self.medialist.lock()
        item = self.medialist.item_at_index(index)
        if item:
            mrl = item.get_mrl()
            del self.mrl_map[mrl]
            self.medialist.remove_index(index)
        item.release()
        self.medialist.unlock()

    def _build_media(self, id, credentials):
        def create_mrl(ids, url):
            for id in ids:
                mrl = url % id
                self.mrl_map[mrl] = int(id)
                yield mrl

        if not isinstance(id, list):
            ids = [id]
        else:
            ids = id
        url = 'http://' + self.target + '/rest/stream.view?id=%s&format="raw"&' + str(credentials)
        media = [self.instance.media_new(mrl) for mrl in create_mrl(ids, url)]
        return media

    def get_volume(self):
        player = self.player.get_media_player()
        volume = player.audio_get_volume() / 100
        player.release()

        return volume if volume <= 1 else 1

    def set_volume(self, volume):
        player = self.player.get_media_player()
        player.audio_set_volume(int(volume * 100))
        player.release()

    def set_position(self, time):
        player = self.player.get_media_player()
        player.set_time(time * 1000)
        player.release()

    def is_playing(self):
        return self.player.is_playing()

    def play(self, index=0):
        self.player.play()
        if index >= 0:
            self.player.play_item_at_index(index)
    
    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.pause()

    def get_index(self):
        if not self.is_playing():
            return -1
        player = self.player.get_media_player()
        mrl = player.get_media().get_mrl()
        player.release()
        id = self.mrl_map[mrl] 
        return id

    def get_position(self):
        player = self.player.get_media_player()
        time_ms = player.get_time()
        player.release()
        return time_ms // 1000

class Credentials(object):
    def __init__(self, dict):
        if 'u' not in dict or 'v' not in dict or 'c' not in dict:
            raise Exception('Missing arguments')
        
        self.dict = dict

        if 'p' in dict:
            self.old = True
        elif 't' in dict and 's' in dict:
            self.old = False
        else:
            raise Exception('Missing arguments')

    def __str__(self):
        args = ['u', 'v', 'c']
        if self.old:
            args.append('p')
        else:
            args.extend(['t', 's'])

        return '&'.join(['%s=%s' % (x, self.dict[x]) for x in args])
