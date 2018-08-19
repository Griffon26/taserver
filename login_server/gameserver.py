import time

from common.connectionhandler import Peer
from common.messages import Login2LauncherSetPlayerLoadoutsMessage, Login2LauncherRemovePlayerLoadoutsMessage


class GameServer(Peer):
    def __init__(self, ip):
        super().__init__()
        self.serverid1 = None
        self.serverid2 = None
        self.ip = ip
        self.port = None
        self.description = None
        self.motd = None
        self.playerbeingkicked = None
        self.joinable = False
        self.match_end_time = None
        self.match_time_counting = False
        self.player_ids = set()

    def set_info(self, port, description, motd):
        self.port = port
        self.description = description
        self.motd = motd
        self.joinable = True

    def set_match_time(self, seconds_remaining, counting):
        self.match_end_time = int(time.time() + seconds_remaining)
        self.match_time_counting = counting

    def get_time_remaining(self):
        if self.match_end_time is not None:
            time_remaining = int(self.match_end_time - time.time())
        else:
            time_remaining = 0

        if time_remaining < 0:
            time_remaining = 0

        return time_remaining

    def set_player_loadouts(self, player):
        msg = Login2LauncherSetPlayerLoadoutsMessage(player.unique_id, player.loadouts.loadout_dict)
        self.send(msg)
        self.player_ids.add(player.unique_id)

    def remove_player_loadouts(self, player):
        msg = Login2LauncherRemovePlayerLoadoutsMessage(player.unique_id)
        self.send(msg)
        self.player_ids.remove(player.unique_id)