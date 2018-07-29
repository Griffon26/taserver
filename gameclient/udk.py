#!/usr/bin/env python3
#
# Copyright (C) 2018  Maurice van der Pot <griffon26@kfk4ever.com>
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

from bitarray import bitarray
import string
import struct

class ParseError(Exception):
    pass

class UnparseableBitsError(ParseError):
    def __init__(self, message, bits):
        super().__init__(message)
        self.bits = bits

class ParserState():
    def __init__(self):
        TrGameReplicationInfoProps = {
            '000000' : { 'name' : 'prefix?',
                         'type' : bitarray,
                         'size' : 5 },
            '011000' : { 'name' : 'm_Flags',
                         'type' : bitarray,
                         'size' : 20 },
            '101000' : { 'name' : 'r_ServerConfig',
                         'type' : bitarray,
                         'size' : 12 },
            '111000' : { 'name' : 'FlagReturnTime',
                         'type' : bitarray,
                         'size' : 41 },
            '011010' : { 'name' : 'ServerName', 'type' : str },
            '111010' : { 'name' : 'TimeLimit', 'type' : int },
            '000110' : { 'name' : 'GoalScore', 'type' : int },
            '100110' : { 'name' : 'RemainingMinute', 'type' : int },
            '010110' : { 'name' : 'ElapsedTime', 'type' : int },
            '110110' : { 'name' : 'RemainingTime', 'type' : int },
            '111110' : { 'name' : 'bStopCountDown', 'type' : bool },
            '000001' : { 'name' : 'GameClass', 'type' : int },
            '100001' : { 'name' : 'MessageOfTheDay', 'type' : str },
            '010001' : { 'name' : 'RulesString',
                         'type' : bitarray,
                         'size' : 544 },
            '001001' : { 'name' : 'FlagState',
                         'type' : bitarray,
                         'size' : 10,
                         'values' : { '0000000000' : 'Enemy flag on stand',
                                      '0000000001' : 'Enemy flag taken',
                                      '0000000011' : 'Enemy flag dropped',
                                      '1000000000' : 'Own flag on stand',
                                      '1000000001' : 'Own flag taken',
                                      '1000000011' : 'Own flag dropped' } },
            '111001' : { 'name' : 'bAllowKeyboardAndMouse', 'type' : bool },
            '010101' : { 'name' : 'bWarmupRound', 'type' : bool },
            '001101' : { 'name' : 'MinNetPlayers', 'type' : int },
            '101111' : { 'name' : 'r_nBlip',
                         'type' : bitarray,
                         'size' : 8 },
        }

        TrFlagCTFProps = {
            '111011' : { 'name' : 'Team',
                         'type' : bitarray,
                         'size' : 10 },
        }

        TrPlayerReplicationInfoProps = {
            '000000' : { 'name' : 'prefix?',
                         'type' : bitarray,
                         'size' : 5 },
            '101010' : { 'name' : 'UniqueId',
                         'type' : bitarray,
                         'size' : 64 },
            '110110' : { 'name' : 'bWaitingPlayer', 'type' : bool },
            '000110' : { 'name' : 'bBot', 'type' : bool },
            '101110' : { 'name' : 'bIsSpectator', 'type' : bool },
            '111110' : { 'name' : 'Team (11 bits)',
                         'type' : bitarray,
                         'size' : 11,
                         'values' : { '10001000000' : 'DiamondSword',
                                      '11110000000' : 'BloodEagle' } },
            '000001' : { 'name' : 'PlayerID', 'type' : int },
            '100001' : { 'name' : 'PlayerName', 'type' : str },
            '110001' : { 'name' : 'Deaths', 'type' : int },
            '011001' : { 'name' : 'CharClassInfo', 'type' : int },
            '000011' : { 'name' : 'r_VoiceClass', 'type' : int },
            '000111' : { 'name' : 'm_nPlayerIconIndex', 'type' : int },
            '001111' : { 'name' : 'm_PendingBaseClass', 'type' : int },
            '101111' : { 'name' : 'm_CurrentBaseClass', 'type' : int },
        }

        self.class_dict = {
            '00110100101111010100000000000000' : { 'name' : 'TrFlagCTF_DiamondSword',
                                                   'props' : TrFlagCTFProps },
            '00100111010010011000000000000000' : { 'name' : 'UTTeamInfo',
                                                   'props' : {} },
            '00100100101111010100000000000000' : { 'name' : 'TrFlagCTF_BloodEagle',
                                                   'props' : TrFlagCTFProps },
            '00000110101111001100000000000000' : { 'name' : 'TrPlayerReplicationInfo',
                                                   'props' : TrPlayerReplicationInfoProps },
            '00110001010000010100000000000000' : { 'name' : 'TrPlayerController',
                                                   'props' : {} },
            '01110001101110110100000000000000' : { 'name' : 'TrGameReplicationInfo',
                                                   'props' : TrGameReplicationInfoProps },
            '00000101100101011110000000000000' : { 'name' : 'WorldInfo',
                                                   'props' : {} },
            '00010011100001101100000000000000' : { 'name' : 'TrServerSettingsInfo',
                                                   'props' : {} },
            '00111100001100100100000000000000' : { 'name' : 'TrBaseTurret_DiamondSword',
                                                   'props' : {} },
            '01001010100010101100000000000000' : { 'name' : 'TrRadarStation_DiamondSword',
                                                   'props' : {} },
            '00110111000101011110000000000000' : { 'name' : 'TrCTFBase_DiamondSword',
                                                   'props' : {} },
            '01100110100101011110000000000000' : { 'name' : 'TrVehicleStation_DiamondSword',
                                                   'props' : {} },
            '01001011110100001100000000000000' : { 'name' : 'TrInventoryStationCollision',
                                                   'props' : {} },
            '00000000110010101100000000000000' : { 'name' : 'TrRepairStationCollision',
                                                   'props' : {} },
            '00111010100001100100000000000000' : { 'name' : 'TrPlayerPawn',
                                                   'props' : {} },
            '01111100101110010100000000000000' : { 'name' : 'TrDevice_LightSpinfusor',
                                                   'props' : {} },
            '01101100101110010100000000000000' : { 'name' : 'TrDevice_LightAssaultRifle',
                                                   'props' : {} },
            '01100101110110010100000000000000' : { 'name' : 'TrDevice_GrenadeLauncher_Light',
                                                   'props' : {} },
            '01001000101110010100000000000000' : { 'name' : 'TrDevice_LaserTargeter',
                                                   'props' : {} },
            '01111000100110010100000000000000' : { 'name' : 'TrDevice_Blink',
                                                   'props' : {} },
            '01000011100110010100000000000000' : { 'name' : 'TrDevice_ConcussionGrenade',
                                                   'props' : {} },
            '00100111101110010100000000000000' : { 'name' : 'TrDevice_Melee_DS',
                                                   'props' : {} },
            '01101101010100001100000000000000' : { 'name' : 'TrInventoryManager',
                                                   'props' : {} },
            '00000011110100001100000000000000' : { 'name' : 'TrStationCollision',
                                                   'props' : {} },
            '00011100001100100100000000000000' : { 'name' : 'TrBaseTurret_BloodEagle',
                                                   'props' : {} },
            '01110010100010101100000000000000' : { 'name' : 'TrRadarStation_BloodEagle',
                                                   'props' : {} },
            '00100110100101011110000000000000' : { 'name' : 'TrVehicleStation_BloodEagle',
                                                   'props' : {} },
            '00111100100101011110000000000000' : { 'name' : 'TrPowerGenerator_BloodEagle',
                                                   'props' : {} },
            '01010111000101011110000000000000' : { 'name' : 'TrCTFBase_BloodEagle',
                                                   'props' : {} },
        }

        self.instance_count = {}
        self.channels = {}


def int2bitarray(n, nbits):
    bits = bitarray(endian='little')
    bits.frombytes(struct.pack('<L', n))
    return bits[:nbits]

def toint(bits):
    zerobytes = bytes( (0,0,0,0) )
    longbytes = (bits.tobytes() + zerobytes)[0:4]
    return struct.unpack('<L', longbytes)[0]

def getnbits(n, bits):
    if n > len(bits):
        raise EOFError
    #print('got %s' % bits[0:n].to01())
    return bits[0:n], bits[n:]

def getstring(bits):
    stringbytes = bits.tobytes()
    result = []
    for b in stringbytes:
        if b != 0:
            result.append(chr(b))
        else:
            break

    return ''.join(result), bits[(len(result) + 1) * 8:]

class PropertyValueMultipleChoice():
    def __init__(self):
        self.value = None
        self.valuebits = None

    @classmethod
    def frombitarray(cls, bits, size, values, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        property_value = PropertyValueMultipleChoice()
        
        property_value.valuebits, bits = getnbits(size, bits)
        property_value.value = values.get(property_value.valuebits.to01(), 'Unknown')

        return property_value, bits

    def tobitarray(self):
        return self.valuebits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return '%s%s (%s)\n' % (indent_prefix,
                                self.valuebits.to01(),
                                self.value)

class PropertyValueString():
    def __init__(self):
        self.value = None

    @classmethod
    def frombitarray(cls, bits, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        property_value = PropertyValueString()
        
        stringsizebits, bits = getnbits(32, bits)
        stringsize = toint(stringsizebits)

        if stringsize > 0:
            property_value.value, bits = getstring(bits)

            if len(property_value.value) + 1 != stringsize:
                raise ParseError('ERROR: string size (%d) was not equal to expected size (%d)' %
                                 (len(property_value.value) + 1,
                                  stringsize))
        else:
            property_value.value = ''

        return property_value, bits

    def tobitarray(self):
        bits = int2bitarray(len(self.value), 32)
        bits.frombytes(bytes(self.value, encoding = 'latin1'))
        bits.extend('00000000')
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return '%sx (%s)\n' % (indent_prefix,
                               self.value)

class PropertyValueInt():
    def __init__(self):
        self.value = None

    @classmethod
    def frombitarray(cls, bits, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        property_value = PropertyValueInt()
        
        propertyvaluebits, bits = getnbits(32, bits)
        property_value.value = toint(propertyvaluebits)

        return property_value, bits

    def tobitarray(self):
        return int2bitarray(self.value, 32)
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return '%s%s (%d)\n' % (indent_prefix,
                                self.tobitarray().to01(),
                                self.value)

class PropertyValueBool():
    def __init__(self):
        self.value = None

    @classmethod
    def frombitarray(cls, bits, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        property_value = PropertyValueBool()
        
        propertyvaluebits, bits = getnbits(1, bits)
        property_value.value = (propertyvaluebits[0] == 1)

        return property_value, bits

    def tobitarray(self):
        return bitarray(self.value)

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return '%s%s\n' % (indent_prefix, '1' if self.value else '0')
        
class PropertyValueBitarray():
    def __init__(self):
        self.value = None

    @classmethod
    def frombitarray(cls, bits, size, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        property_value = PropertyValueBitarray()
        
        property_value.value, bits = getnbits(size, bits)

        return property_value, bits

    def tobitarray(self):
        return self.value

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return '%s%s\n' % (indent_prefix, self.value.to01())
        
class ObjectProperty():
    def __init__(self):
        self.propertyid = None
        self.value = None

    @classmethod
    def frombitarray(cls, bits, class_, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        object_property = ObjectProperty()
        
        propertyidbits, bits = getnbits(6, bits)
        object_property.propertyid = toint(propertyidbits)
        
        propertykey = propertyidbits.to01()
        property_ = class_['props'].get(propertykey, {'name' : 'Unknown'})
        object_property.property_ = property_

        propertytype = property_.get('type', None)
        propertysize = property_.get('size', None)
        propertyvalues = property_.get('values', None)
        if propertyvalues:
            object_property.value = PropertyValueMultipleChoice.frombitarray(bits, propertysize, propertyvalues)
        
        elif propertytype:
            if propertytype is str:
                object_property.value, bits = \
                    PropertyValueString.frombitarray(bits, debug = debug)
            elif propertytype is int:
                object_property.value, bits = \
                    PropertyValueInt.frombitarray(bits, debug = debug)
            elif propertytype is bool:
                object_property.value, bits = \
                    PropertyValueBool.frombitarray(bits, debug = debug)
            elif propertytype is bitarray:
                object_property.value, bits = \
                    PropertyValueBitarray.frombitarray(bits, propertysize, debug = debug)
            else:
                raise RuntimeError('Coding error')
            
        else:
            raise UnparseableBitsError('Unknown property %s for class %s' %
                                       (propertykey, class_['name']),
                                       bits)
        
        return object_property, bits

    def tobitarray(self):
        bits = int2bitarray(self.propertyid, 6)
        bits.extend(self.value.tobitarray())
        return bits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        propertykey = int2bitarray(self.propertyid, 6).to01()
        text = '%s%s (property = %s)\n' % (indent_prefix,
                                           propertykey,
                                           self.property_['name'])
        text += self.value.tostring(indent = indent + len(propertykey))
        return text

class ObjectInstance():
    def __init__(self):
        self.class_ = None
        self.name = None
        self.properties = []
    
    @classmethod
    def frombitarray(cls, bits, object_class, channel, state, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        object_instance = ObjectInstance()

        object_instance.object_class = object_class
        class_ = state.class_dict[object_class.getclasskey()]
        
        classname = class_['name']
        
        if channel not in state.channels:
            state.instance_count[classname] = state.instance_count.get(classname, -1) + 1
            instancename = '%s_%d' % (classname, state.instance_count[classname])
            state.channels[channel] = { 'class' : class_,
                                        'instancename' : instancename }

        object_instance.name = state.channels[channel]['instancename']

        while bits:
            property_, bits = ObjectProperty.frombitarray(bits, class_, debug = debug)
            object_instance.properties.append(property_)

        return object_instance, bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        for prop in self.properties:
            bits.extend(prop.tobitarray())
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        text = '%s%s (object %s)\n' % (indent_prefix,
                                       self.object_class.getclasskey(),
                                       self.name)
        for prop in self.properties:
            text += prop.tostring(indent + len(self.object_class.getclasskey()))
        return text

class ObjectClass():
    def __init__(self):
        self.classid = None

    def getclasskey(self):
        return int2bitarray(self.classid, 32).to01()

    @classmethod
    def frombitarray(cls, bits, state, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        object_class = ObjectClass()
        
        classbits, bits = getnbits(32, bits)
        object_class.classid = toint(classbits)
        
        classkey = classbits.to01()
        if classkey not in state.class_dict:
            classname = 'unknown%d' % len(state.class_dict)
            state.class_dict[classkey] = { 'name' : classname,
                                           'props' : {} }

        return object_class, bits

    def tobitarray(self):
        return int2bitarray(self.classid, 32)

class PayloadData():
    def __init__(self):
        self.object_class = None
        self.instance = None
        self.error = None
        self.payload = None

    @classmethod
    def frombitarray(cls, bits, channel, state, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        payload_data = PayloadData()
        
        payloadsizebits, bits = getnbits(14, bits)
        payloadsize = toint(payloadsizebits)
        
        payloadbits, bits = getnbits(payloadsize, bits)
        originalpayloadbits = bitarray(payloadbits)

        try:
            payload_data.object_class, payloadbits = \
                ObjectClass.frombitarray(payloadbits,
                                         state,
                                         debug = debug)
            
            payload_data.instance, payloadbits = \
                ObjectInstance.frombitarray(payloadbits,
                                            payload_data.object_class,
                                            channel,
                                            state,
                                            debug = debug)
            
            if payloadbits:
                payload_data.error = 'Bits of payload left over: %s' % payloadbits.to01()
            
        except UnparseableBitsError as e:
            payload_data.error = '%s, bits left: %s' % (str(e), e.bits.to01())
            payload_data.payload = originalpayloadbits

        return payload_data, bits

    def tobitarray(self):
        if not self.error:
            databits = self.object_class.tobitarray() + self.instance.tobitarray()
        else:
            databits = self.payload
        bits = int2bitarray(len(databits), 14)
        bits.extend(databits)
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        if not self.error:
            payloadsize = len(self.object_class.tobitarray() +
                              self.instance.tobitarray())
        else:
            payloadsize = len(self.payload)
        items.append('%s (payloadsize = %d)\n' % (int2bitarray(payloadsize, 14).to01(),
                                                  payloadsize))
        text = ''.join(['%s%s' % (indent_prefix, item) for item in items])
        indent += 14
        if self.error:
            text += ' ' * indent + self.payload.to01() + ' (unparseable)\n'
        else:
            text += self.instance.tostring(indent = indent)
        return text

class ChannelData():
    def __init__(self):
        self.channel = None
        self.counter = None
        self.unknownbits = None
        self.payload = None

    @classmethod
    def frombitarray(cls, bits, with_counter, state, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        channel_data = ChannelData()
        channelbits, bits = getnbits(10, bits)
        channel_data.channel = toint(channelbits)

        if with_counter:
            counterbits, bits = getnbits(5, bits)
            channel_data.counter = toint(counterbits)

            channel_data.unknownbits, bits = getnbits(8, bits)

        channel_data.payload, bits = PayloadData.frombitarray(bits,
                                                              channel_data.channel,
                                                              state,
                                                              debug = debug)

        return channel_data, bits

    def tobitarray(self):
        bits = int2bitarray(self.channel, 10)
        if self.counter is not None:
            bits.extend(int2bitarray(self.counter, 5))
            bits.extend(self.unknownbits)
        bits.extend(self.payload.tobitarray())
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        items.append('%s (channel = %d)\n' % (int2bitarray(self.channel, 10).to01(),
                                              self.channel))
        indent += 10
        if self.counter is not None:
            items.append('          %s (counter = %d)\n' %
                         (int2bitarray(self.counter, 5).to01(),
                          self.counter))
            items.append('               %s\n' % self.unknownbits.to01())
            indent += 13
        text = ''.join(['%s%s' % (indent_prefix, item) for item in items])
        text += self.payload.tostring(indent = indent)
        return text

class PacketData():
    def __init__(self):
        self.unknownbits11 = False
        self.unknownbits10 = bitarray()
        self.channeldata = None

    @classmethod
    def frombitarray(cls, bits, state, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        packet_data = PacketData()

        flag1a, bits = getnbits(2, bits)
        if flag1a == bitarray('11'):
            packet_data.unknownbits11 = True
            flag1a, bits = getnbits(2, bits)

        if flag1a == bitarray('00'):
            channel_with_counter = False
        elif flag1a == bitarray('01'):
            channel_with_counter = True
        elif flag1a == bitarray('10'):
            packet_data.unknownbits10, bits = getnbits(2, bits)
            if packet_data.unknownbits10 != bitarray('11'):
                raise ParseError('Unexpected value for unknownbits10')
            channel_with_counter = True
        else:
            raise ParseError('Unexpected value for flag1a')

        packet_data.channel_data, bits = ChannelData.frombitarray(bits,
                                                                  channel_with_counter,
                                                                  state,
                                                                  debug = debug)
            
        return packet_data, bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        if self.unknownbits11:
            bits.extend('11')
        if self.channel_data.counter is None:
            bits.extend('00')
        elif self.unknownbits10:
            bits.extend('10')
            bits.extend(self.unknownbits10)
        else:
            bits.extend('01')

        bits.extend(self.channel_data.tobitarray())

        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        if self.unknownbits11:
            items.append('11\n')
        if self.channel_data.counter is None:
            items.append('00\n')
        elif self.unknownbits10:
            items.append('10\n')
            items.append('%s\n' % self.unknownbits10.to01())
        else:
            items.append('01\n')
        text = ''.join(['%s%s' % (indent_prefix, item) for item in items])
        text += self.channel_data.tostring(indent = indent + 2)
        return text

class PacketAck():
    def __init__(self):
        self.acknr = None

    @classmethod
    def frombitarray(cls, bits, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)

        packet_ack = PacketAck()
            
        acknrbits, bits = getnbits(14, bits)
        packet_ack.acknr = toint(acknrbits)

        return packet_ack, bits

    def tobitarray(self):
        return int2bitarray(self.acknr, 14)

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return ('%s%s (acknr = %d)\n' % (indent_prefix,
                                         self.tobitarray().to01(),
                                         self.acknr))

class Packet():
    def __init__(self, seqnr):
        self.seqnr = seqnr
        self.parts = []
        self.leftoverbits = bitarray()

    @classmethod
    def frombitarray(cls, bits, state, debug = False):
        if debug:
            print('%s::frombitarray' % cls.__name__)
            
        seqnr, bits = getnbits(14, bits)
        packet = Packet(toint(seqnr))

        while bits:
            flag1, bits = getnbits(1, bits)
            if flag1 == bitarray('0'):
                part, bits = PacketData.frombitarray(bits, state, debug = debug)
                packet.parts.append(part)
            elif len(bits) >= 14:
                part, bits = PacketAck.frombitarray(bits, debug = debug)
                packet.parts.append(part)
            else:
                # the end
                break

        return packet, bits

    def tobitarray(self):
        bits = int2bitarray(self.seqnr, 14)
        for part in self.parts:
            if isinstance(part, PacketData):
                bits.extend('0')
            else:
                bits.extend('1')
            bits.extend(part.tobitarray())
        bits.extend('1')
        return bits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        size = (len(self.tobitarray()) + 7) / 8
        text = []
        text.append('%sPacket with size %d\n' % (indent_prefix, size))
        text.append('%s%s (seqnr = %d)\n' % (indent_prefix,
                                             int2bitarray(self.seqnr, 14).to01(),
                                             self.seqnr))

        indent = indent + 14
        indent_prefix = ' ' * indent
        for part in self.parts:
            if isinstance(part, PacketData):
                text.append('%s0\n' % indent_prefix)
            else:
                text.append('%s1\n' % indent_prefix)
            text.append(part.tostring(indent = indent + 1))

        text.append('%s1\n' % indent_prefix)
        text.append('full packet: %s\n' % self.tobitarray().to01())
        return ''.join(text)

class Parser():
    def __init__(self):
        self.parser_state = ParserState()

    def parsepacket(self, bits, debug = False):
        packet, bits = Packet.frombitarray(bits, self.parser_state, debug = False)
        if len(bits) >= 8:
            raise UnparseableBitsError('More than 8 bits were left after parsing', bits)
        return packet
            

            

