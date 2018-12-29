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
    def __init__(self, message, bitsleft):
        super().__init__(message)
        self.bitsleft = bitsleft

class ParserState():
    def __init__(self):
        TrInventoryStationCollisionProps = {
            '101100' : { 'name' : 'RelativeLocation2',
                         'type' : bitarray,
                         'size' : 2 },
            '001001' : { 'name' : 'RelativeLocation',
                         'type' : bitarray,
                         'size' : 10 },
            '011111' : { 'name': 'Base',
                         'type': bitarray,
                         'size': 30},
        }
        TrPowerGeneratorProps = {
            '111110' : { 'name' : 'r_MaxHealth',
                         'type' : bitarray,
                         'size' : 31 }
        }

        TrPlayerControllerProps = {
            '101010' : { 'name' : 'PlayerReplicationInfo',
                         'type' : bitarray,
                         'size' : 13 }
        }

        TrBaseTurretProps = {
            '110001' : { 'name' : 'r_FlashCount',
                         'type' : bitarray,
                         'size' : 8 }
        }

        TrProj_BaseTurretProps = {
            '011100' : { 'name' : 'Rotation',
                         'type' : bitarray,
                         'size' : 18 },
            '000001' : { 'name' : 'Velocity',
                         'type' : bitarray,
                         'size' : 42 }
        }

        TrDroppedPickupProps = {
            '101101' : { 'name' : 'InventoryClass',
                         'type' : bitarray,
                         'size' : 31 },
            '011101' : { 'name' : 'Base',
                         'type' : bitarray,
                         'size' : 30 },
            '110011' : { 'name' : 'Rotation',
                         'type' : bitarray,
                         'size' : 10 },
            '101011' : { 'name' : 'bFadeOut',
                         'type' : 'flag' }
        }

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
            '110000' : { 'name' : 'bHardAttach', 'type' : 'flag'},
            '000100' : { 'name' : 'Physics',
                         'type' : bitarray,
                         'size' : 3 },
            '000010' : { 'name' : 'Location',
                         'type' : bitarray,
                         'size' : 51 },
            '110010' : { 'name' : 'Rotation',
                         'type' : bitarray,
                         'size' : 10 },
            '001010' : { 'name' : 'Velocity',
                         'type' : bitarray,
                         'size' : 39 },
            '101110' : { 'name' : 'Base',
                         'type' : bitarray,
                         'size' : 9 },
            '100001' : { 'name' : 'bCollideActors', 'type' : 'flag'},
            '010001' : { 'name' : 'bCollideWorld', 'type' : 'flag'},
            '111011' : { 'name' : 'Team',
                         'type' : bitarray,
                         'size' : 10 },
            '000111' : { 'name' : 'HolderPRI',
                         'type' : bitarray,
                         'size' : 10 }
        }

        TrPlayerReplicationInfoProps = {
            '000000' : { 'name' : 'prefix?',
                         'type' : bitarray,
                         'size' : 5 },
            '000010' : { 'name' : 'Location',
                         'type' : bitarray,
                         'size' : 51 },
            '110010' : { 'name' : 'Rotation',
                         'type' : bitarray,
                         'size' : 10 },
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
            '001001' : { 'name' : 'Score', 'type' : int },
            '011001' : { 'name' : 'CharClassInfo', 'type' : int },
            '010101' : { 'name' : 'bHasFlag', 'type': bool},
            '101101' : { 'name' : 'r_bSkinId', 'type': int},
            '111101' : { 'name' : 'r_EquipLevels',
                         'type' : bitarray,
                         'size' : 48},
            '000011' : { 'name' : 'r_VoiceClass', 'type': int},
            '001011' : { 'name' : 'm_nPlayerClassId', 'type': int},
            '101011' : { 'name' : 'm_nCreditsEarned', 'type': int},
            '000111' : { 'name' : 'm_nPlayerIconIndex', 'type': int},
            '001111' : { 'name' : 'm_PendingBaseClass', 'type': int},
            '101111' : { 'name' : 'm_CurrentBaseClass', 'type': int},

        }

        FirstClientObjectProps = {
            '000100' : { 'name' : 'prop8',
                         'type' : bitarray,
                         'size' : 162 },
        }                

        FirstServerObjectProps = {
            '111000' : { 'name' : 'mysteryproperty',
                         'type' : PropertyValueMystery },
        }                

        self.class_dict = {
            '01111010010000101100000000000000' : { 'name' : 'TrProj_BaseTurret',
                                                   'props' : TrProj_BaseTurretProps },
            '01001011001001010100000000000000' : { 'name' : 'TrDroppedPickup',
                                                   'props' : TrDroppedPickupProps },
            '00110100101111010100000000000000' : { 'name' : 'TrFlagCTF_DiamondSword',
                                                   'props' : TrFlagCTFProps },
            '00100111010010011000000000000000' : { 'name' : 'UTTeamInfo',
                                                   'props' : {} },
            '00100100101111010100000000000000' : { 'name' : 'TrFlagCTF_BloodEagle',
                                                   'props' : TrFlagCTFProps },
            '00000110101111001100000000000000' : { 'name' : 'TrPlayerReplicationInfo',
                                                   'props' : TrPlayerReplicationInfoProps },
            '00110001010000010100000000000000' : { 'name' : 'TrPlayerController',
                                                   'props' : TrPlayerControllerProps },
            '01110001101110110100000000000000' : { 'name' : 'TrGameReplicationInfo',
                                                   'props' : TrGameReplicationInfoProps },
            '00000101100101011110000000000000' : { 'name' : 'WorldInfo',
                                                   'props' : {} },
            '00010011100001101100000000000000' : { 'name' : 'TrServerSettingsInfo',
                                                   'props' : {} },
            '00111100001100100100000000000000' : { 'name' : 'TrBaseTurret_DiamondSword',
                                                   'props' : TrBaseTurretProps },
            '01001010100010101100000000000000' : { 'name' : 'TrRadarStation_DiamondSword',
                                                   'props' : {} },
            '00110111000101011110000000000000' : { 'name' : 'TrCTFBase_DiamondSword',
                                                   'props' : {} },
            '01100110100101011110000000000000' : { 'name' : 'TrVehicleStation_DiamondSword',
                                                   'props' : {} },
            '01111100100101011110000000000000' : { 'name' : 'TrPowerGenerator_DiamondSword',
                                                   'props' : TrPowerGeneratorProps },
            '01001011110100001100000000000000' : { 'name' : 'TrInventoryStationCollision',
                                                   'props' : TrInventoryStationCollisionProps },
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
                                                   'props' : TrBaseTurretProps },
            '01110010100010101100000000000000' : { 'name' : 'TrRadarStation_BloodEagle',
                                                   'props' : {} },
            '00100110100101011110000000000000' : { 'name' : 'TrVehicleStation_BloodEagle',
                                                   'props' : {} },
            '00111100100101011110000000000000' : { 'name' : 'TrPowerGenerator_BloodEagle',
                                                   'props' : {} },
            '01010111000101011110000000000000' : { 'name' : 'TrCTFBase_BloodEagle',
                                                   'props' : {} },
            '00001000100000000111111011011000' : { 'name' : 'FirstClientObject',
                                                   'props' : FirstClientObjectProps },
            '10001000000000000000000000000000' : { 'name' : 'FirstServerObject',
                                                   'props' : FirstServerObjectProps },
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
        raise ParseError('Tried to get more bits (%d) than are available (%d)' %
                             (n, len(bits)),
                         bits)
    
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

def debugbits(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        bitsbefore = args[1]
        debug = kwargs['debug']

        if debug:
            print('%s::frombitarray (entry): starting with %s%s' %
                  (self.__class__.__name__,
                   bitsbefore.to01()[0:32],
                   '...' if len(bitsbefore) > 32 else ' EOF'))
        bitsafter = func(*args, **kwargs)

        if debug:
            nbits_consumed = len(bitsbefore) - len(bitsafter)
            if bitsbefore[nbits_consumed:] != bitsafter:
                raise RuntimeError('Function not returning a tail of the input bits')
            print('%s::frombitarray (exit) : consumed \'%s\'' %
                  (self.__class__.__name__, bitsbefore.to01()[:nbits_consumed]))

            if bitsbefore[:nbits_consumed] != self.tobitarray():
                raise RuntimeError('Object %s serialized into bits is not equal to bits parsed:\n' % self.__name__ +
                                   'in : %s\n' % bitsbefore[:nbits_consumed].to01() +
                                   'out: %s\n' % self.tobitarray().to01())

        return bitsafter
    
    return wrapper

class PropertyValueMultipleChoice():
    def __init__(self):
        self.value = None
        self.valuebits = None

    @debugbits
    def frombitarray(self, bits, size, values, debug = False):
        self.valuebits, bits = getnbits(size, bits)
        self.value = values.get(self.valuebits.to01(), 'Unknown')
        return bits

    def tobitarray(self):
        return self.valuebits if self.value is not None else bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value = %s)\n' % (indent_prefix,
                                            self.valuebits.to01(),
                                            self.value)
        else:
            text = '%sempty\n' % indent_prefix
        return text

class PropertyValueString():
    def __init__(self):
        self.size = None
        self.value = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        stringsizebits, bits = getnbits(32, bits)
        self.size = toint(stringsizebits)

        if self.size > 0:
            self.value, bits = getstring(bits)

            if len(self.value) + 1 != self.size:
                raise ParseError('ERROR: string size (%d) was not equal to expected size (%d)' %
                                     (len(self.value) + 1,
                                      self.size),
                                 bits)
        else:
            self.value = ''

        return bits

    def tobitarray(self):
        if self.value is not None:
            bits = int2bitarray(self.size, 32)
            if self.size > 0:
                bits.frombytes(bytes(self.value, encoding = 'latin1'))
                bits.extend('00000000')
        else:
            bits = bitarray()
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (strsize = %d)\n' % (indent_prefix, int2bitarray(self.size, 32).to01(), self.size)

            if self.size > 0:
                indent_prefix += ' ' * 32        
                text += '%sx (value = "%s")\n' % (indent_prefix,
                                                  self.value)
        else:
            text = '%sempty\n' % indent_prefix
            
        return text

class PropertyValueVector():
    def __init__(self):
        self.short1 = None
        self.short2 = None
        self.short3 = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        valuebits, bits = getnbits(16, bits)
        self.short1 = toint(valuebits)
        valuebits, bits = getnbits(16, bits)
        self.short2 = toint(valuebits)
        valuebits, bits = getnbits(16, bits)
        self.short3 = toint(valuebits)
        return bits

    def tobitarray(self):
        if self.short3 is not None:
            return (int2bitarray(self.short1, 16) +
                    int2bitarray(self.short2, 16) +
                    int2bitarray(self.short3, 16))
        else:
            return bitarray()
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.short3 is not None:
            return '%s%s (value = (%d,%d,%d))\n' % (indent_prefix,
                                                    self.tobitarray().to01(),
                                                    self.short1,
                                                    self.short2,
                                                    self.short3)
        else:
            return '%sempty\n' % indent_prefix

class PropertyValueInt():
    def __init__(self):
        self.value = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        valuebits, bits = getnbits(32, bits)
        self.value = toint(valuebits)
        return bits

    def tobitarray(self):
        return int2bitarray(self.value, 32) if self.value is not None else bitarray()
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value = %d)\n' % (indent_prefix,
                                            self.tobitarray().to01(),
                                            self.value)
        else:
            text = '%sempty\n' % indent_prefix
        return text

class PropertyValueBool():
    def __init__(self):
        self.value = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        valuebits, bits = getnbits(1, bits)
        self.value = (valuebits[0] == 1)
        return bits

    def tobitarray(self):
        return bitarray([self.value]) if self.value is not None else bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value = %s)\n' % (indent_prefix,
                                            '1' if self.value else '0',
                                            self.value)
        else:
            text = '%sempty\n' % indent_prefix
        return text

class PropertyValueFlag():
    def __init__(self):
        pass

    @debugbits
    def frombitarray(self, bits, debug = False):
        return bits

    def tobitarray(self):
        return bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        text = '%s(flag is set)\n' % indent_prefix
        return text
        
class PropertyValueBitarray():
    def __init__(self):
        self.value = None

    @debugbits
    def frombitarray(self, bits, size, debug = False):
        self.value, bits = getnbits(size, bits)
        return bits

    def tobitarray(self):
        return self.value if self.value is not None else bitarray()

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        if self.value is not None:
            text = '%s%s (value)\n' % (indent_prefix, self.value.to01())
        else:
            text = '%sempty\n' % indent_prefix
        return text

class PropertyValueMystery():
    def __init__(self):
        self.bitarray = PropertyValueBitarray()
        self.string1 = PropertyValueString()
        self.determinator = PropertyValueInt()
        self.int1 = PropertyValueInt()
        self.int2 = PropertyValueInt()
        self.vector = PropertyValueVector()
        self.string2 = PropertyValueString()
            
    @debugbits
    def frombitarray(self, bits, debug = False):
        bits = self.bitarray.frombitarray(bits, 130, debug = debug)
        bits = self.string1.frombitarray(bits, debug = debug)
        bits = self.determinator.frombitarray(bits, debug = debug)
        if self.determinator.value == 0:
            bits = self.int1.frombitarray(bits, debug = debug)
        else:
            bits = self.vector.frombitarray(bits, debug = debug)
        bits = self.int2.frombitarray(bits, debug = debug)
        bits = self.string2.frombitarray(bits, debug = debug)
        
        return bits

    def tobitarray(self):
        return (self.bitarray.tobitarray() +
                self.string1.tobitarray() +
                self.determinator.tobitarray() +
                (self.int1.tobitarray() if self.determinator.value == 0 else self.vector.tobitarray()) +
                self.int2.tobitarray() +
                self.string2.tobitarray())

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        items.append(self.bitarray.tostring(indent))
        items.append(self.string1.tostring(indent))
        items.append(self.determinator.tostring(indent))
        if self.determinator.value == 0:
            items.append(self.int1.tostring(indent))
        else:
            items.append(self.vector.tostring(indent))
        items.append(self.int2.tostring(indent))
        items.append(self.string2.tostring(indent))
        text = ''.join(items)
        return text
        
class ObjectProperty():
    def __init__(self):
        self.propertyid = None
        self.property_ = { 'name' : 'Unknown' }
        self.value = None

    @debugbits
    def frombitarray(self, bits, class_, debug = False):
        propertyidbits, bits = getnbits(6, bits)
        self.propertyid = toint(propertyidbits)
        
        propertykey = propertyidbits.to01()
        property_ = class_['props'].get(propertykey, {'name' : 'Unknown'})
        self.property_ = property_

        propertytype = property_.get('type', None)
        propertysize = property_.get('size', None)
        propertyvalues = property_.get('values', None)
        if propertyvalues:
            self.value = PropertyValueMultipleChoice()
            bits = self.value.frombitarray(bits, propertysize, propertyvalues, debug = debug)
        
        elif propertytype:
            if propertytype is str:
                self.value = PropertyValueString()
                bits = self.value.frombitarray(bits, debug = debug)
            elif propertytype is int:
                self.value = PropertyValueInt()
                bits = self.value.frombitarray(bits, debug = debug)
            elif propertytype is bool:
                self.value = PropertyValueBool()
                bits = self.value.frombitarray(bits, debug = debug)
            elif propertytype is 'flag':
                self.value = PropertyValueFlag()
                bits = self.value.frombitarray(bits, debug = debug)
            elif propertytype is bitarray:
                self.value = PropertyValueBitarray()
                bits = self.value.frombitarray(bits, propertysize, debug = debug)
            elif propertytype == PropertyValueMystery:
                self.value = PropertyValueMystery()
                bits = self.value.frombitarray(bits, debug = debug)                
            else:
                raise RuntimeError('Coding error')
            
        else:
            raise ParseError('Unknown property %s for class %s' %
                                 (propertykey, class_['name']),
                             bits)
        
        return bits

    def tobitarray(self):
        bits = bitarray(endian='little')
        if self.propertyid is not None:
            bits.extend(int2bitarray(self.propertyid, 6))
        if self.value is not None:
            bits.extend(self.value.tobitarray())
        return bits

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        text = ''
        if self.propertyid is not None:
            propertykey = int2bitarray(self.propertyid, 6).to01()
            text += '%s%s (property = %s)\n' % (indent_prefix,
                                               propertykey,
                                               self.property_['name'])
        if self.value is not None:
            text += self.value.tostring(indent = indent + len(propertykey))
        return text

class ObjectInstance():
    def __init__(self):
        self.class_ = None
        self.properties = []
    
    @debugbits
    def frombitarray(self, bits, class_, state, debug = False):
        
        while bits:
            property_ = ObjectProperty()
            self.properties.append(property_)
            bits = property_.frombitarray(bits, class_, debug = debug)

        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        for prop in self.properties:
            bits.extend(prop.tobitarray())
        return bits
    
    def tostring(self, indent = 0):
        items = [prop.tostring(indent) for prop in self.properties]
        return ''.join(items)

class ObjectClass():
    def __init__(self):
        self.classid = None

    def getclasskey(self):
        return int2bitarray(self.classid, 32).to01()

    @debugbits
    def frombitarray(self, bits, state, debug = False):
        classbits, bits = getnbits(32, bits)
        self.classid = toint(classbits)
        
        classkey = classbits.to01()
        if classkey not in state.class_dict:
            classname = 'unknown%d' % len(state.class_dict)
            state.class_dict[classkey] = { 'name' : classname,
                                           'props' : {} }

        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        if self.classid is not None:
            bits.extend(int2bitarray(self.classid, 32))
        return bits

class PayloadData():
    def __init__(self):
        self.size = None
        self.object_class = None
        self.object_deleted = False
        self.instancename = None
        self.instance = None
        self.bitsleftreason = None
        self.bitsleft = None

    @debugbits
    def frombitarray(self, bits, channel, state, debug = False):
        payloadsizebits, bits = getnbits(14, bits)
        self.size = toint(payloadsizebits)
        
        payloadbits, bits = getnbits(self.size, bits)
        originalpayloadbits = bitarray(payloadbits)

        try:
            if channel not in state.channels:
                self.object_class = ObjectClass()
                payloadbits = self.object_class.frombitarray(payloadbits, state, debug = debug)

                class_ = state.class_dict[self.object_class.getclasskey()]
                classname = class_['name']

                state.instance_count[classname] = state.instance_count.get(classname, -1) + 1
                instancename = '%s_%d' % (classname, state.instance_count[classname])
                state.channels[channel] = { 'class' : class_,
                                            'instancename' : instancename }
            else:
                class_ = state.channels[channel]['class']
                instancename = state.channels[channel]['instancename']

            self.instancename = instancename
            self.instance = ObjectInstance()
            payloadbits = self.instance.frombitarray(payloadbits, class_, state, debug = debug)
            
            if payloadbits:
                raise ParseError('Bits of payload left over',
                                 payloadbits)

            if self.size == 0:
                self.object_deleted = True
                del state.channels[channel]
            
        except ParseError as e:
            self.bitsleftreason = str(e)
            self.bitsleft = e.bitsleft

        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')

        if self.size is not None:
            bits.extend(int2bitarray(self.size, 14))
        if self.object_class is not None:
            bits.extend(self.object_class.tobitarray())
        if self.instance is not None:
            bits.extend(self.instance.tobitarray())
        if self.bitsleft is not None:
            bits.extend(self.bitsleft)
            
        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        text = ''

        if self.size is not None:      
            text += ('%s%s (payloadsize = %d)\n' % (indent_prefix,
                                                    int2bitarray(self.size, 14).to01(),
                                                    self.size))
            indent += 14
            
        if self.object_class is not None:
            text += '%s%s (new object %s)\n' % (' ' * indent,
                                                self.object_class.tobitarray().to01(),
                                                self.instancename)
            indent += 32
        elif self.object_deleted:
            text += '%sx (destroyed object = %s)\n' % (' ' * indent,
                                                       self.instancename)
            indent += 1
        else:
            text += '%sx (object = %s)\n' % (' ' * indent,
                                             self.instancename)
            indent += 1

        if self.instance is not None:
            text += self.instance.tostring(indent = indent)
            
        if self.bitsleft is not None:
            text += ' ' * indent + self.bitsleft.to01() + ' (rest of payload)\n'
            
        return text

class ChannelData():
    def __init__(self):
        self.channel = None
        self.counter = None
        self.unknownbits = None
        self.payload = None

    @debugbits
    def frombitarray(self, bits, with_counter, state, debug = False):
        channelbits, bits = getnbits(10, bits)
        self.channel = toint(channelbits)

        if with_counter:
            counterbits, bits = getnbits(5, bits)
            self.counter = toint(counterbits)

            self.unknownbits, bits = getnbits(8, bits)

        self.payload = PayloadData()
        bits = self.payload.frombitarray(bits, self.channel, state, debug = debug)
        return bits

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
        self.flag1a = None
        self.unknownbits11 = None
        self.unknownbits10 = None
        self.channel_data = None

    @debugbits
    def frombitarray(self, bits, state, debug = False):

        self.flag1a, bits = getnbits(2, bits)
        if self.flag1a == bitarray('11'):
            self.unknownbits11 = True
            self.flag1a = None
            self.flag1a, bits = getnbits(2, bits)

        if self.flag1a == bitarray('00'):
            channel_with_counter = False
        elif self.flag1a == bitarray('01'):
            channel_with_counter = True
        elif self.flag1a == bitarray('10'):
            channel_with_counter = True
            self.unknownbits10, bits = getnbits(2, bits)
            if self.unknownbits10 != bitarray('11'):
                raise ParseError('Unexpected value for unknownbits10: %s' %
                                     self.unknownbits10.to01(),
                                 bits)
            
        else:
            raise ParseError('Unexpected value for flag1a: %s' % self.flag1a.to01(),
                             bits)

        self.channel_data = ChannelData()
        bits = self.channel_data.frombitarray(bits, channel_with_counter, state, debug = debug)
            
        return bits

    def tobitarray(self):
        bits = bitarray(endian = 'little')
        if self.unknownbits11:
            bits.extend('11')
        if self.flag1a:
            bits.extend(self.flag1a)
        if self.unknownbits10 is not None:
            bits.extend(self.unknownbits10)

        if self.channel_data:
            bits.extend(self.channel_data.tobitarray())

        return bits
    
    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        items = []
        if self.unknownbits11 is not None:
            items.append('11 (flag1a = 3)\n')
        if self.flag1a is not None:
            items.append('%s (flag1a = %d)\n' % (self.flag1a.to01(),
                                                 toint(self.flag1a)))
        if self.unknownbits10 is not None:
            items.append('%s\n' % self.unknownbits10.to01())
                         
        text = ''.join(['%s%s' % (indent_prefix, item) for item in items])
        if self.channel_data is not None:
            text += self.channel_data.tostring(indent = indent + 2)
        return text

class PacketAck():
    def __init__(self):
        self.acknr = None

    @debugbits
    def frombitarray(self, bits, debug = False):
        acknrbits, bits = getnbits(14, bits)
        self.acknr = toint(acknrbits)
        return bits

    def tobitarray(self):
        return int2bitarray(self.acknr, 14)

    def tostring(self, indent = 0):
        indent_prefix = ' ' * indent
        return ('%s%s (acknr = %d)\n' % (indent_prefix,
                                         self.tobitarray().to01(),
                                         self.acknr))

class Packet():
    def __init__(self):
        self.seqnr = None
        self.parts = []
        self.paddingbits = None

    @debugbits
    def frombitarray(self, bits, state, debug = False):
        original_nbits = len(bits)
        
        seqnr, bits = getnbits(14, bits)
        self.seqnr = toint(seqnr)

        while bits:
            flag1, bits = getnbits(1, bits)
            if flag1 == bitarray('0'):
                part = PacketData()
                self.parts.append(part)
                bits = part.frombitarray(bits, state, debug = debug)
            elif len(bits) >= 14:
                part = PacketAck()
                self.parts.append(part)
                bits = part.frombitarray(bits, debug = debug)
            else:
                # the end
                break

        parsed_nbits = len(self.tobitarray())

        if len(bits) != original_nbits - parsed_nbits:
            raise RuntimeError('Coding error: parsed bits + unparsed bits does not equal total bits')

        nr_of_padding_bits = 8 - (parsed_nbits % 8)
        if len(bits) != nr_of_padding_bits:
            raise ParseError('Left over bits at the end of the packet',
                             bits)

        self.paddingbits, bits = getnbits(nr_of_padding_bits, bits)

        # No need to return bits, because if we didn't parse everything
        # we would have raised an exception anyway
        return None

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
        
        databits = self.tobitarray()
        packetbits = bitarray(databits)
        packetbits.fill()
        size = len(packetbits) / 8
        
        text = []
        text.append('%sPacket with size %d\n' % (indent_prefix, size))
        if self.seqnr is not None:
            text.append('%s%s (seqnr = %d)\n' % (indent_prefix,
                                                 int2bitarray(self.seqnr, 14).to01(),
                                                 self.seqnr))

            indent = indent + 14
            
        indent_prefix = ' ' * indent
        for part in self.parts:
            if isinstance(part, PacketData):
                text.append('%s0 (flag1 = 0)\n' % indent_prefix)
            else:
                text.append('%s1 (flag1 = 1)\n' % indent_prefix)
            text.append(part.tostring(indent = indent + 1))
            
        if self.paddingbits:
            text.append('%s1 (flag1 = 1)\n' % indent_prefix)
            text.append('    Bits left over in the last byte: %s\n' % self.paddingbits.to01())
        
        return ''.join(text)

class Parser():
    def __init__(self):
        self.parser_state = ParserState()

    def parsepacket(self, bits, debug = False, exception_on_failure = True):
        packet = Packet()
        bitsleft = None
        errormsg = None
        try:
            packet.frombitarray(bits, self.parser_state, debug = debug)
        except ParseError as e:
            errormsg = str(e)
            bitsleft = e.bitsleft
            if exception_on_failure:
                raise

        if exception_on_failure:
            return packet
        else:
            return packet, bitsleft, errormsg
