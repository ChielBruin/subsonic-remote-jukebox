import vlc

class Jukebox(object):
    def __init__(self, target):
        self.target = target
        self.instance = vlc.Instance()
        
        self.medialist = vlc.MediaList()
        self.player = vlc.MediaListPlayer(self.instance)
        self.player.set_media_player(self.instance.media_player_new())
        self.player.set_media_list(self.medialist)

        self.playlist = []

    def set(self, id, credentials):
        (media, ids) = self._build_media(id, credentials)
        
        # Create new list
        self.playlist = ids
        self.medialist = vlc.MediaList()
        self.player.stop()
        self.player.set_media_list(self.medialist)

        self.medialist.lock()
        for media_item in media:
            self.medialist.add_media(media_item)
        self.medialist.unlock()

    def add(self, id, credentials):
        (media, ids) = self._build_media(id, credentials)

        self.playlist.extend(ids)
        self.medialist.lock()
        for media_item in media:
            self.medialist.add_media(media_item)
        self.medialist.unlock()

    def _build_media(self, id, credentials):
        if not isinstance(id, list):
            ids = [id]
        else:
            ids = id
        url = 'http://' + self.target + '/rest/stream.view?id=%s&format="raw"&' + str(credentials)
        media = [self.instance.media_new(url % id) for id in ids]
        return (media, ids)

    def get_volume(self):
        player = self.player.get_media_player()
        volume = player.audio_get_volume() / 100
        player.release()

        return volume if volume <= 1 else 1

    def set_volume(self, volume):
        player = self.player.get_media_player()
        player.audio_set_volume(int(volume * 100))
        player.release()

    def is_playing(self):
        return self.player.is_playing()

    def play(self, index=-1):
        self.player.play()
        if index >= 0:
            self.player.play_item_at_index(index)
    
    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.pause()

    def get_index(self):
        return 89 # The Gereg 

    def get_position(self):
        return 20

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
