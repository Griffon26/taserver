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

import datetime

from common.datatypes import *
from common.game_items import get_game_setting_modes, get_class_menu_data_modded_defs, get_unmodded_class_menu_data
from common.messages import Message, Client2LoginConnect, Client2LoginSwitchMode, \
    Login2ClientModeInfo, Login2ClientMenuData, Login2ClientLoadouts, Client2LoginLoadoutChange, \
    Login2AuthChatMessage, parse_message_from_string
from .player_state import PlayerState, handles, handles_control_message
from common import utils


class AuthenticatedState(PlayerState):

    @handles(packet=a0033)
    def handle_a0033(self, request):
        self.player.send(a0033())

    def on_enter(self):
        self.logger.info("%s is entering state %s" % (self.player, type(self).__name__))
        self.player.friends.notify_online()

    def on_exit(self):
        self.logger.info("%s is exiting state %s" % (self.player, type(self).__name__))

    @handles(packet=a00d5)
    def handle_a00d5(self, request):
        if request.findbytype(m0228).value == 1:
            self.player.send(originalfragment(0x1EEB3, 0x20A10))  # 00d5 (map list)
        else:
            self.player.send(a00d5().setservers(self.player.login_server
                                                .all_game_servers()
                                                .values(),
                                                self.player.address_pair))  # 00d5 (server list)

    @handles(packet=a0014)
    def handle_a0014(self, request):
        self.player.send(a0014().setclasses(get_unmodded_class_menu_data().classes.values()))

    @handles(packet=a018b)
    def handle_a018b(self, request):
        self.player.send(originalfragment(0x20B47, 0x20B4B))  # 018b

    @handles(packet=a01b5)
    def handle_a01b5(self, request):
        self.player.send(a01b5().add_watch_now_menu())

    @handles(packet=a0176)
    def handle_a0176(self, request):
        self.player.send(originalfragment(0x218FF, 0x219D1))  # 0176

    @handles(packet=a0177)
    def handle_menu(self, request):
        menu_part = request.findbytype(m02ab).value
        menu_fragments = {
            PURCHASE_TYPE_SERVER: originalfragment(0x38d17, 0x3d0fe),
            0x01ed: a0177().setdata(0x01ed, get_unmodded_class_menu_data().class_purchases, False),  # Classes
            0x01f0: a0177().setdata(0x01f0, {item
                                             for _, class_items
                                             in get_unmodded_class_menu_data().class_items.items()
                                             for item
                                             in class_items.weapons},
                                    False),  # Weapons with categories
            0x01f1: originalfragment(0x54bc6, 0x54db0),  # Purpose not fully known, needed or weapons are locked
            0x01f2: a0177().setdata(0x01f2, {item
                                             for _, class_items
                                             in get_unmodded_class_menu_data().class_items.items()
                                             for item
                                             in class_items.belt_items},
                                    False),  # Belt items
            0x01f3: a0177().setdata(0x01f3, {item
                                             for _, class_items
                                             in get_unmodded_class_menu_data().class_items.items()
                                             for item
                                             in class_items.packs},
                                    False),  # Packs
            0x01f4: originalfragment(0x5a776, 0x6fde3),  # Item upgrades
            # 0x01f6: originalfragment(0x5965a, 0x5a72b),  # Perks
            0x01f6: a0177().setdata(0x01f6, {item
                                             for item
                                             in get_unmodded_class_menu_data().perks},
                                    False),  # Perks
            0x01f7: originalfragment(0x5a733, 0x5a76e),
            0x01f8: originalfragment(0x5737d, 0x579af),  # Armor Upgrades
            0x01f9: a0177().setdata(0x01f9, {item
                                             for _, class_items
                                             in get_unmodded_class_menu_data().class_items.items()
                                             for item
                                             in class_items.skins},
                                    False),  # Skins
            0x01fa: originalfragment(0x221a6, 0x22723),
            0x01fb: originalfragment(0x2272b, 0x235b8),
            PURCHASE_TYPE_BOOSTERS: originalfragment(0x235c0, 0x239dd),
            PURCHASE_TYPE_NAME: originalfragment(0x239e5, 0x23acf),  # Name change
            0x0206: originalfragment(0x2620e, 0x28ac1),
            0x0214: originalfragment(0x23ad7, 0x26206),  # Purchaseable loadouts
            0x0218: originalfragment(0x28ac9, 0x2f4d7),
            # Weapon name <-> ID mapping - Probably only need to construct this at some point if we wanted to add entirely new weapons
            0x021b: originalfragment(0x3d106, 0x47586),
            0x021c: originalfragment(0x6fdeb, 0x6fecf),
            0x0220: a0177().setdata(0x0220, {item
                                             for item
                                             in get_unmodded_class_menu_data().voices},
                                    False),  # Voices
            PURCHASE_TYPE_TAG: originalfragment(0x2f4df, 0x2f69f),  # Modify Clantag
            0x0227: originalfragment(0x2f6a7, 0x38d0f),  # GOTY
        }
        if menu_part in menu_fragments:
            self.player.send(menu_fragments[menu_part])
        return True

    @handles(packet=a00b1)
    def handle_server_join_first_step(self, request):
        server_field = request.findbytype(m02c7)
        if not server_field:
            self._send_private_msg_from_server(self.player, 'Quick match is not yet supported. '
                                                            'Please select a server to join instead.')
        else:
            game_server = self.player.login_server.find_server_by_id(server_field.value)

            allowed_to_join = True
            join_message = STDMSG_JOINED_A_MATCH_QUEUE

            if self.player.is_modded:
                if game_server.game_setting_mode != self.player.player_settings.game_setting_mode:
                    # Cannot join a goty server in ootb mode or vice versa
                    self._send_private_msg_from_server(self.player, 'You are in %s mode; you cannot join a %s mode server' %
                                                       (self.player.player_settings.game_setting_mode,
                                                        game_server.game_setting_mode))
                    allowed_to_join = False
                    join_message = STDMSG_UNABLE_TO_CONNECT_TO_SERVER
            else:
                # Disallow joining a non-ootb server if the player is not known to be modded
                if game_server.game_setting_mode != 'ootb':
                    self._send_private_msg_from_server(self.player, 'You cannot join a %s server without TAMods' %
                                                       game_server.game_setting_mode)
                    allowed_to_join = False
                    join_message = STDMSG_UNABLE_TO_CONNECT_TO_SERVER

            if not game_server.joinable:
                allowed_to_join = False
                join_message = STDMSG_CANNOT_CONNECT_TO_SERVER

            if allowed_to_join and game_server.password_hash is not None:
                password_attempt = request.findbytype(m032e)
                if password_attempt is None or bytes(password_attempt.content) != game_server.password_hash:
                    allowed_to_join = False
                    join_message = STDMSG_INCORRECT_PASSWORD

            b0msg = a00b0().set_server(game_server).set_player(self.player.unique_id)
            if allowed_to_join:
                b0msg.setlength(9)
                b0msg.findbytype(m042a).set(2)
                self.player.send(b0msg)
                self.player.send(a0070().set([
                    m0348().set(self.player.unique_id),
                    m0095(),
                    m009e().set(MESSAGE_UNKNOWNTYPE),
                    m009d().set(self.player.unique_id),
                    m02fc().set(join_message)
                ]))

                b0msg = a00b0().setlength(10).set_server(game_server).set_player(self.player.unique_id)
                b0msg.findbytype(m042a).set(2)
                self.player.send(b0msg)

                b4msg = a00b4().set_server(game_server).set_player(self.player.unique_id)
                b4msg.findbytype(m042a).set(3)
                self.player.send(b4msg)
            else:
                b0msg.content.append(m042b().set(join_message))
                self.player.send(b0msg)
                self.player.send(a0070().set([
                    m0348().set(self.player.unique_id),
                    m0095(),
                    m009e().set(MESSAGE_UNKNOWNTYPE),
                    m009d().set(self.player.unique_id),
                    m02fc().set(join_message)
                ]))

    @handles(packet=a00b2)
    def handle_server_join_second_step(self, request):
        # Import here to avoid a circular import dependency
        from .on_game_server_state import OnGameServerState

        match_id = request.findbytype(m02c4).value
        game_server = self.player.login_server.find_server_by_match_id(match_id)

        if game_server.joinable:
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
            request.content.append(m06de().set(self.player.player_settings.clan_tag))

            if self.player.game_server and self.player.team is not None:
                self.player.game_server.send_all_players_on_team(request,
                                                                 self.player.team)

        elif message_type == MESSAGE_PRIVATE:
            addressed_player_name = request.findbytype(m034a).value
            addressed_player = self.player.login_server.find_player_by_display_name(addressed_player_name)
            if addressed_player:
                request.content.append(m02fe().set(self.player.display_name))
                request.content.append(m06de().set(self.player.player_settings.clan_tag))
                self.player.send(request)

                if addressed_player.unique_id == utils.AUTHBOT_ID:
                    message_text = request.findbytype(m02e6).value
                    addressed_player.peer.send(Login2AuthChatMessage(self.player.login_name,
                                                                     self.player.verified,
                                                                     message_text))
                else:
                    request.findbytype(m034a).set(addressed_player.display_name)
                    addressed_player.send(request)
            else:
                reply = a0070().set([
                    m009e().set(MESSAGE_UNKNOWNTYPE),
                    m02fc().set(STDMSG_PLAYER_NOT_FOUND_ONLINE),
                    m034a().set(addressed_player_name)
                ])
                self.player.send(reply)

        elif message_type == MESSAGE_CONTROL:
            try:
                msg = parse_message_from_string(request.findbytype(m02e6).value)
            except (ValueError, RuntimeError) as e:
                self.logger.warning('Failed to parse control message: %s' % str(e))
                return
            # Handle the control message
            self.handle_control_message(msg)

        else:  # MESSAGE_PUBLIC
            request.content.append(m02fe().set(self.player.display_name))
            request.content.append(m06de().set(self.player.player_settings.clan_tag))

            # Uncomment this to easily print a mapping between message IDs and message texts
            # (only works when a map is loaded)
            # text = request.findbytype(m02e6).value
            # if text.startswith('msg'):
            #     _, idtext = text.split(' ')
            #     msgid = int(idtext, 16)
            #     for i in range(msgid, msgid + 64):
            #         self.player.send(a0070().set([
            #             m0348().set(self.player.unique_id),
            #             m0095(),
            #             m009e().set(MESSAGE_PUBLIC),
            #             m009d().set(self.player.unique_id),
            #             m02e6().set('msg = %X' % i),
            #         ]))
            #         self.player.send(a0070().set([
            #             m0348().set(self.player.unique_id),
            #             m0095(),
            #             m009e().set(MESSAGE_UNKNOWNTYPE),
            #             m009d().set(self.player.unique_id),
            #             m02fc().set(i)
            #         ]))

            if self.player.game_server:
                self.player.game_server.inspect_message_for_map_vote(self.player, request.findbytype(m02e6).value)
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

    def _send_control_message(self, player, message: Message):
        msg = a0070().set([
            m009e().set(MESSAGE_CONTROL),
            m02e6().set(message.to_string()),
            m034a().set(player.display_name),
            m0574(),
            m02fe().set('taserver'),
            m06de().set('bot')
        ])
        player.send(msg)

    @handles(packet=a0175)
    def handle_purchase_or_promo_code(self, request):
        promotion_code = request.findbytype(m0669)
        if promotion_code:
            self._handle_verification_code(promotion_code.value)
        else:
            purchase_type = request.findbytype(m02ab).value
            if purchase_type == PURCHASE_TYPE_TAG:
                self._handle_purchase_tag(request)
            else:
                # not implemented
                pass

    def _handle_verification_code(self, authcode):
        if (self.player.login_name in self.player.login_server.accounts and
                self.player.login_server.accounts[self.player.login_name].authcode == authcode):

            self.player.login_server.accounts[self.player.login_name].password_hash = self.player.password_hash
            self.player.login_server.accounts[self.player.login_name].authcode = None
            self.player.login_server.accounts.save()

            self._send_private_msg_from_server(self.player, 'Verification successful. Now restart Tribes.')
        else:
            invalid_code_msg = a0175()
            invalid_code_msg.findbytype(m0442).set_success(False)
            invalid_code_msg.findbytype(m02fc).set(STDMSG_NOT_A_VALID_PROMOTION_CODE)  # message type
            invalid_code_msg.findbytype(m0669).set(authcode)
            self.player.send(invalid_code_msg)

    def is_valid_clan_tag(self, clan_tag):
        if len(clan_tag) > 4:
            return False

        try:
            ascii_bytes = clan_tag.encode('ascii')
        except UnicodeError:
            return False

        if not utils.is_valid_ascii_for_name(ascii_bytes):
            return False

        return True

    def _handle_purchase_tag(self, request):
        purchase_item = request.findbytype(m04d9).value

        if purchase_item == PURCHASE_ITEM_CHANGE_TAG:
            tag_field = request.findbytype(m02fe)

            if tag_field and self.is_valid_clan_tag(tag_field.value):
                self.player.player_settings.clan_tag = tag_field.value

                tag_change_msg = a006d().set([
                    m0348().set(self.player.unique_id),
                    m06de().set(self.player.player_settings.clan_tag)
                ])
                self.player.send(tag_change_msg)

                reply_msg = a0175().set([
                    m0442().set_success(True),
                    m02fc().set(0),
                    request.findbytype(m05cf),
                    request.findbytype(m02ab),
                    request.findbytype(m04d9),
                    request.findbytype(m05cc),
                    request.findbytype(m035a),
                    m0683().set(7)
                ])
                self.player.send(reply_msg)
            else:
                reply_msg = a0175().set([
                    m0442().set_success(False),
                    m02fc().set(STDMSG_THAT_NAME_MAY_NOT_BE_USED),
                    request.findbytype(m05cf),
                    request.findbytype(m02ab),
                    request.findbytype(m04d9),
                    request.findbytype(m05cc),
                    request.findbytype(m035a),
                    m0683().set(6),
                    m049e().set(1)
                ])
                self.player.send(reply_msg)

        else: # remove tag

            self.player.player_settings.clan_tag = ''

            tag_change_msg = a006d().set([
                m0348().set(self.player.unique_id),
                m06de().set(self.player.player_settings.clan_tag)
            ])
            self.player.send(tag_change_msg)

            reply_msg = a0175().set([
                m0442().set_success(True),
                m02fc().set(0),
                request.findbytype(m05cf),
                request.findbytype(m02ab),
                request.findbytype(m04d9),
                request.findbytype(m05cc),
                request.findbytype(m035a),
                m0683().set(7)
            ])
            self.player.send(reply_msg)

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
                    if self.player.get_unmodded_loadouts().is_loadout_menu_item(menu_area_field.value):
                        equip_value = int(int_field.value) if int_field else string_field.value
                        self.player.get_unmodded_loadouts().modify(menu_area_field.value, setting, equip_value)
                        loadout_changed = True
                    elif menu_area_field.value == MENU_AREA_SETTINGS:
                        # Ignore user settings. They'll have to store them themselves
                        pass
                    else:
                        value = int_field.value if int_field else string_field.value
                        self.logger.debug('******* Setting %08X of menu area %s to value %s'
                                          % (setting, menu_area_field.value, value))
                else:
                    value = int_field.value if int_field else string_field.value
                    self.logger.debug('******* Setting %08X to value %s' % (setting, value))

            if self.player.game_server and loadout_changed:
                self.player.game_server.set_player_loadouts(self.player)

    @handles(packet=a01c6)
    def handle_request_for_server_info(self, request):
        server_id = request.findbytype(m02c7).value
        game_server = self.player.login_server.find_server_by_id(server_id)
        if game_server.joinable:
            players = self.player.login_server.find_players_by(game_server=game_server)
            reply = a01c6()
            reply.content = [
                m02c7().set(server_id),
                m0228().set(0x00000002),
                m00e9().setservers([game_server], self.player.address_pair).setplayers(players)
            ]
            self.player.send(reply)

    @handles(packet=a011b)
    def handle_edit_friend_list(self, request):
        if self.player.verified:
            add = request.findbytype(m0592).value
            if add:
                name = request.findbytype(m034a).value
                # TODO: also make this work for verified players that are offline
                other_player = self.player.login_server.find_player_by_display_name(name)

                reply = None
                if other_player and other_player.verified:
                    if not self.player.friends.add(other_player.unique_id, name):
                        request.content.extend([
                            m0442().set_success(False),
                            m02fc().set(STDMSG_PLAYER_X_IS_ALREADY_YOUR_FRIEND)
                        ])
                        reply = request
                else:
                    request.content.extend([
                        m0442().set_success(False),
                        m02fc().set(STDMSG_PLAYER_X_NOT_FOUND)
                    ])
                    reply = request

                if reply:
                    self.player.send(reply)

            else:  # remove
                unique_id = request.findbytype(m020d).value
                self.player.friends.remove(unique_id)

    @handles(packet=a011c)
    def handle_request_for_friend_list(self, request):
        assert request.content == []

        if self.player.verified:
            self.player.login_server.social_network.send_friend_list(self.player.unique_id)

    def _send_game_mode_data(self):
        # Send the control message indicating the switch
        mode_info = Login2ClientModeInfo(self.player.player_settings.game_setting_mode)
        self._send_control_message(self.player, mode_info)

        # Give the player the appropriate class menu data1
        menu_data_datetime = datetime.datetime.utcnow()
        for data_point in get_class_menu_data_modded_defs(self.player.player_settings.game_setting_mode):
            menu_data = Login2ClientMenuData(data_point, menu_data_datetime)
            self._send_control_message(self.player, menu_data)

        for loadout_point in self.player.get_loadout_modded_defs():
            loadout_data = Login2ClientLoadouts(loadout_point)
            self._send_control_message(self.player, loadout_data)

    @handles_control_message(messageType=Client2LoginConnect)
    def handle_client2login_connect(self, message: Client2LoginConnect):
        # The player is now known to be modded
        self.player.is_modded = True
        self._send_game_mode_data()

    @handles_control_message(messageType=Client2LoginSwitchMode)
    def handle_client2login_switchmode(self, message: Client2LoginSwitchMode):
        modes = list(get_game_setting_modes())
        next_mode = modes[(modes.index(self.player.player_settings.game_setting_mode) + 1) % len(modes)]
        self.player.player_settings.game_setting_mode = next_mode

        # Send the player a message confirming their mode
        self._send_private_msg_from_server(self.player, 'You are now in %s mode'
                                           % self.player.player_settings.game_setting_mode)
        self._send_game_mode_data()

    @handles_control_message(messageType=Client2LoginLoadoutChange)
    def handle_client2login_loadoutchange(self, message: Client2LoginLoadoutChange):
        # Modify the player's loadout
        self.player.get_current_loadouts().modify_by_class_details(message.game_class, message.loadout_index,
                                                     message.loadout_slot, message.value)
        # Send the change to the game server the player is in
        if self.player.game_server:
            self.player.game_server.set_player_loadouts(self.player)
