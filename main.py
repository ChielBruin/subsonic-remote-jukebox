from jukebox import Jukebox
from relayServer import RelayServer

def main():
    actual_server_location = '192.168.1.71:4040'
    
    jukebox = Jukebox(actual_server_location)
    RelayServer.init(actual_server_location, jukebox)
    RelayServer.start(4040)

if __name__ == '__main__':
    main()
