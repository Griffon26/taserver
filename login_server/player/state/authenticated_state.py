#!/usr/bin/env python3
#
# Copyright (C) 2018  Maurice van der Pot <griffon26@kfk4ever.com>,
# Copyright (C) 2018 Timo Pomer <timopomer@gmail.com>
#
# This file is part of taserver
#
# taserver is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# taserver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with taserver.  If not, see <http://www.gnu.org/licenses/>.
#

from common.game_items import class_menu_data
from ...datatypes import *
from ..friends import FRIEND_STATE_VISIBLE
from .player_state import PlayerState, handles


class AuthenticatedState(PlayerState):
    @handles(packet=a0033)
    def handle_a0033(self, request):
        self.player.send(a0033())

    def on_exit(self):
        self.logger.info("%s is exiting state %s" % (self.player, type(self).__name__))
        self.player.save()

    @handles(packet=a00d5)
    def handle_a00d5(self, request):
        if request.findbytype(m0228).value == 1:
            self.player.send(originalfragment(0x1EEB3, 0x20A10))  # 00d5 (map list)
        else:
            self.player.send(a00d5().setservers(self.player.login_server.game_servers.values(),
                                                self.player.address_pair))  # 00d5 (server list)

    @handles(packet=a0014)
    def handle_a0014(self, request):
        # self.player.send(originalfragment(0x20A18, 0x20B3F))  # 0014 (class list)
        self.player.send(a0014().setclasses(class_menu_data.classes.values()))

    @handles(packet=a018b)
    def handle_a018b(self, request):
        self.player.send(originalfragment(0x20B47, 0x20B4B))  # 018b

    @handles(packet=a01b5)
    def handle_a01b5(self, request):
        self.player.send(originalfragment(0x20B53, 0x218F7))  # 01b5 (watch now)

    @handles(packet=a0176)
    def handle_a0176(self, request):
        self.player.send(originalfragment(0x218FF, 0x219D1))  # 0176

    @handles(packet=a0177)
    def handle_menu(self, request):
        menu_part = request.findbytype(m02ab).value
        menu_fragments = {
            0x01de: originalfragment(0x38d17, 0x3d0fe),
            0x01ed: a0177().setdata(0x01ed, class_menu_data.class_purchases, False),  # Classes
            0x01f0: a0177().setdata(0x01f0, {item
                                             for _, class_items
                                             in class_menu_data.class_items.items()
                                             for item
                                             in class_items.weapons},
                                    False),  # Weapons with categories
            0x01f1: originalfragment(0x54bc6, 0x54db0),  # Purpose not fully known, needed or weapons are locked
            0x01f2: a0177().setdata(0x01f2, {item
                                             for _, class_items
                                             in class_menu_data.class_items.items()
                                             for item
                                             in class_items.belt_items},
                                    False),  # Belt items
            0x01f3: a0177().setdata(0x01f3, {item
                                             for _, class_items
                                             in class_menu_data.class_items.items()
                                             for item
                                             in class_items.packs},
                                    False),  # Packs
            0x01f4: originalfragment(0x5a776, 0x6fde3),  # Item upgrades
            # 0x01f6: originalfragment(0x5965a, 0x5a72b),  # Perks
            0x01f6: a0177().setdata(0x01f6, {item
                                             for item
                                             in class_menu_data.perks},
                                    False),  # Perks
            0x01f7: originalfragment(0x5a733, 0x5a76e),
            0x01f8: originalfragment(0x5737d, 0x579af),  # Armor Upgrades
            0x01f9: a0177().setdata(0x01f9, {item
                                             for _, class_items
                                             in class_menu_data.class_items.items()
                                             for item
                                             in class_items.skins},
                                    False),  # Skins
            0x01fa: originalfragment(0x221a6, 0x22723),
            0x01fb: originalfragment(0x2272b, 0x235b8),
            0x01fc: originalfragment(0x235c0, 0x239dd),
            0x0200: originalfragment(0x239e5, 0x23acf),  # Name change
            0x0206: originalfragment(0x2620e, 0x28ac1),
            0x0214: originalfragment(0x23ad7, 0x26206),  # Purchaseable loadouts
            0x0218: originalfragment(0x28ac9, 0x2f4d7),  # Weapon name <-> ID mapping - Probably only need to construct this at some point if we wanted to add entirely new weapons
            0x021b: originalfragment(0x3d106, 0x47586),
            0x021c: originalfragment(0x6fdeb, 0x6fecf),
            0x0220: a0177().setdata(0x0220, {item
                                             for item
                                             in class_menu_data.voices},
                                    False),  # Voices
            0x0221: originalfragment(0x2f4df, 0x2f69f),  # Modify Clantag
            0x0227: originalfragment(0x2f6a7, 0x38d0f),  # GOTY
        }
        if menu_part in menu_fragments:
            self.player.send(menu_fragments[menu_part])

    @handles(packet=a00b1)
    def handle_server_join_first_step(self, request):
        server_field = request.findbytype(m02c7)
        if not server_field:
            self._send_private_msg_from_server(self.player, 'Quick match is not yet supported. '
                                                            'Please select a server to join instead.')
        else:
            game_server = self.player.login_server.find_server_by_id(server_field.value)

            b0msg = a00b0().setlength(9).set_server(game_server).set_player(self.player.unique_id)
            b0msg.findbytype(m042a).set(2)
            self.player.send(b0msg)

            self.player.send(a0070().set([
                 m0348().set(self.player.unique_id),
                 m0095(),
                 m009e().set(MESSAGE_UNKNOWNTYPE),
                 m009d().set(self.player.unique_id),
                 m02fc().set(STDMSG_JOINED_A_MATCH_QUEUE)
            ]))

            b0msg = a00b0().setlength(10).set_server(game_server).set_player(self.player.unique_id)
            b0msg.findbytype(m042a).set(2)
            self.player.send(b0msg)

            b4msg = a00b4().set_server(game_server).set_player(self.player.unique_id)
            b4msg.findbytype(m042a).set(3)
            self.player.send(b4msg)

    @handles(packet=a00b2)
    def handle_server_join_second_step(self, request):
        # Import here to avoid a circular import dependency
        from .on_game_server_state import OnGameServerState

        match_id = request.findbytype(m02c4).value
        game_server = self.player.login_server.find_server_by_match_id(match_id)
        b0msg = a00b0().setlength(10).set_server(game_server).set_player(self.player.unique_id)
        b0msg.findbytype(m042a).set(7)
        self.player.send(b0msg)
        self.player.send(a0035().setserverdata(game_server, self.player.address_pair))

        self.player.set_state(OnGameServerState, game_server)

    @handles(packet=a0070)
    def handle_chat(self, request):
        message_type = request.findbytype(m009e).value

        if message_type == MESSAGE_TEAM:
            request.content.append(m02fe().set(self.player.display_name))
            request.content.append(m06de().set(self.player.tag))

            if self.player.game_server and self.player.team is not None:
                self.player.game_server.send_all_players_on_team(request,
                                                                 self.player.team)

        elif message_type == MESSAGE_PRIVATE:
            addressed_player_name = request.findbytype(m034a).value
            addressed_player = self.player.login_server.find_player_by(display_name=addressed_player_name)
            if addressed_player:
                request.content.append(m02fe().set(self.player.display_name))
                request.content.append(m06de().set(self.player.tag))

                self.player.send(request)

                if self.player.unique_id != addressed_player.unique_id:
                    addressed_player.send(request)

        else:  # MESSAGE_PUBLIC
            request.content.append(m02fe().set(self.player.display_name))
            request.content.append(m06de().set(self.player.tag))

            if self.player.game_server:
                self.player.game_server.send_all_players(request)

    def _send_private_msg_from_server(self, player, text):
        msg = a0070().set([
            m009e().set(MESSAGE_PRIVATE),
            m02e6().set(text),
            m034a().set(player.display_name),
            m0574(),
            m02fe().set('taserver'),
            m06de().set('bot')
        ])
        player.send(msg)

    @handles(packet=a0175)
    def handle_promotion_code_redemption(self, request):
        promotion_code = request.findbytype(m0669)
        if promotion_code:
            authcode = promotion_code.value
            if (self.player.login_name in self.player.login_server.accounts and
                    self.player.login_server.accounts[self.player.login_name].authcode == authcode):

                self.player.login_server.accounts[self.player.login_name].password_hash = self.player.password_hash
                self.player.login_server.accounts[self.player.login_name].authcode = None
                self.player.login_server.accounts.save()
            else:
                invalid_code_msg = a0175()
                invalid_code_msg.findbytype(m02fc).set(STDMSG_NOT_A_VALID_PROMOTION_CODE)  # message type
                invalid_code_msg.findbytype(m0669).set(authcode)
                self.player.send(invalid_code_msg)

    @handles(packet=a006d)
    def handle_menuchange(self, request):
        # Request to change the player's region
        if len(request.content) == 1 and type(request.content[0]) is m0448:
            pass
        else:
            loadout_changed = False
            for arr in request.findbytype(m0144).arrays:
                setting = findbytype(arr, m0369).value
                int_field = findbytype(arr, m0261)
                string_field = findbytype(arr, m0437)

                menu_area_field = findbytype(arr, m0661)

                if menu_area_field:
                    if self.player.loadouts.is_loadout_menu_item(menu_area_field.value):
                        equip_value = int(int_field.value) if int_field else string_field.value
                        self.player.loadouts.modify(menu_area_field.value, setting, equip_value)
                        loadout_changed = True
                    elif menu_area_field.value == MENU_AREA_SETTINGS:
                        # Ignore user settings. They'll have to store them themselves
                        pass
                    else:
                        value = int_field.value if int_field else string_field.value
                        self.logger.debug('******* Setting %08X of menu area %s to value %s' % (setting, menu_area_field.value, value))
                else:
                    value = int_field.value if int_field else string_field.value
                    self.logger.debug('******* Setting %08X to value %s' % (setting, value))

            if self.player.game_server and loadout_changed:
                self.player.game_server.set_player_loadouts(self.player)

    @handles(packet=a01c6)
    def handle_request_for_server_info(self, request):
        server_id = request.findbytype(m02c7).value
        game_server = self.player.login_server.find_server_by_id(server_id)
        players = self.player.login_server.find_players_by(game_server = game_server)
        reply = a01c6()
        reply.content = [
            m02c7().set(server_id),
            m0228().set(0x00000002),
            m00e9().setservers([game_server], self.player.address_pair).setplayers(players)
        ]
        self.player.send(reply)

    @handles(packet=a011b)
    def handle_edit_friend_list(self, request):
        if self.player.registered:
            add = request.findbytype(m0592).value
            if add:
                name = request.findbytype(m034a).value
                # TODO: also make this work for registered players that are offline
                other_player = self.player.login_server.find_player_by(login_name=name)

                if other_player and other_player.registered:
                    self.player.friends.add(other_player.unique_id, name)

            else: # remove
                unique_id = request.findbytype(m020d).value
                self.player.friends.remove(unique_id)

    @handles(packet=a011c)
    def handle_request_for_friend_list(self, request):
        assert request.content == []

        if self.player.registered:

            reply = a011c().set([
                m0348().set(self.player.unique_id),
                m0116().set([[
                    m034a().set(friend['login_name']),
                    m020d().set(friend_id),
                    m0296(),
                    m0591().set(FRIEND_STATE_VISIBLE),
                    m0307()] for friend_id, friend in self.player.friends.friends_dict.items()]
                )
            ])

            self.player.send(reply)
