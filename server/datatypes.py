#!/usr/bin/env python3

import struct

class ParseError(Exception):
    pass

def hexparse(hexstring):
    return bytes([int('0x' + hexbyte, base = 16) for hexbyte in hexstring.split()])

def _originalbytes(start, end):
    with open('tribescapture.bin.stripped', 'rb') as f:
        f.seek(start)
        return f.read(end - start)

#------------------------------------------------------------
# base types
#------------------------------------------------------------

class onebyte():
    def __init__(self, ident, value):
        self.ident = ident
        self.value = value

    def write(self, stream):
        stream.write(struct.pack('<HB', self.ident, self.value))

    def read(self, stream):
        ident, value = struct.unpack('<HB', stream.read(3))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = value
        return self

class twobytes():
    def __init__(self, ident, value):
        self.ident = ident
        self.value = value

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, self.value))

    def read(self, stream):
        ident, value = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = value
        return self

class fourbytes():
    def __init__(self, ident, value):
        self.ident = ident
        self.value = value

    def set(self, value):
        self.value = value
        return self

    def write(self, stream):
        stream.write(struct.pack('<HL', self.ident, self.value))

    def read(self, stream):
        ident, value = struct.unpack('<HL', stream.read(6))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = value
        return self

class nbytes():
    def __init__(self, ident, valuebytes):
        self.ident = ident
        self.value = valuebytes

    def write(self, stream):
        stream.write(struct.pack('<H', self.ident) + self.value)

    def read(self, stream):
        ident = struct.unpack('<H', stream.read(2))[0]
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.value = stream.read(len(self.value))
        return self

class stringenum():
    def __init__(self, ident, text):
        self.ident = ident
        self.text = text

    def set(self, text):
        self.text = text
        return self

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, len(self.text)) + self.text.encode('latin1'))

    def read(self, stream):
        ident, length = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.text = stream.read(length).decode('latin1')
        return self

class arrayofenumblockarrays():
    def __init__(self, ident):
        self.ident = ident
        self.arrays = []

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, len(self.arrays)))
        for arr in self.arrays:
            stream.write(struct.pack('<H', len(arr)))
            for enumfield in arr:
                enumfield.write(stream)

    def read(self, stream):
        ident, length1 = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.arrays = []
        for _ in range(length1):
            innerarray = []
            length2 = struct.unpack('<H', stream.read(2))[0]
            for _ in range(length2):
                enumid = struct.unpack('<H', stream.peek(2))[0]
                classname = ('m%04X' % enumid).lower()
                print('constructing %s' % classname)
                element = globals()[classname]().read(stream)
                innerarray.append(element)
            self.arrays.append(innerarray)
        return self

class enumblockarray():
    def __init__(self, ident):
        self.ident = ident
        self.content = []

    def write(self, stream):
        stream.write(struct.pack('<HH', self.ident, len(self.content)))
        for el in self.content:
            el.write(stream)

    def read(self, stream):
        ident, length = struct.unpack('<HH', stream.read(4))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.content = []
        for i in range(length):
            enumid = struct.unpack('<H', stream.peek(2))[0]
            classname = ('m%04X' % enumid).lower()
            element = globals()[classname]().read(stream)
            self.content.append(element)
        return self

#------------------------------------------------------------
# onebyte
#------------------------------------------------------------

class m02c9(onebyte):
    def __init__(self):
        super(m02c9, self).__init__(0x02c9, 0x00)

class m0326(onebyte):
    def __init__(self):
        super(m0326, self).__init__(0x0326, 0x00)

class m0442(onebyte):
    def __init__(self):
        super(m0442, self).__init__(0x0442, 0x01)

class m05d6(onebyte):
    def __init__(self):
        super(m05d6, self).__init__(0x05d6, 0x00)

class m05e6(onebyte):
    def __init__(self):
        super(m05e6, self).__init__(0x05e6, 0x01)

class m0601(onebyte):
    def __init__(self):
        super(m0601, self).__init__(0x0601, 0x00)

class m0673(onebyte):
    def __init__(self):
        super(m0673, self).__init__(0x0673, 0x00)

class m069b(onebyte):
    def __init__(self):
        super(m069b, self).__init__(0x069b, 0x00)

class m069c(onebyte):
    def __init__(self):
        super(m069c, self).__init__(0x069c, 0x00)

class m0703(onebyte):
    def __init__(self):
        super(m0703, self).__init__(0x0703, 0x00)

#------------------------------------------------------------
# twobytes
#------------------------------------------------------------

class m053d(twobytes):
    def __init__(self):
        super(m053d, self).__init__(0x053d, 0x0000)

class m0600(twobytes):
    def __init__(self):
        super(m0600, self).__init__(0x0600, 0x0003)

#------------------------------------------------------------
# fourbytes
#------------------------------------------------------------

class m0019(fourbytes): 
    def __init__(self): 
        super(m0019, self).__init__(0x0019, 0x00000000) 

class m0035(fourbytes): 
    def __init__(self): 
        super(m0035, self).__init__(0x0035, 0x00000004) 

class m008d(fourbytes): 
    def __init__(self):
        super(m008d, self).__init__(0x008d, 0x00000001)

class m0095(fourbytes): 
    def __init__(self):
        super(m0095, self).__init__(0x0095, 0x00000000)

class m009e(fourbytes): 
    def __init__(self):
        super(m009e, self).__init__(0x009e, 0x00000000)

class m00ba(fourbytes): 
    def __init__(self):
        super(m00ba, self).__init__(0x00ba, 0x00030ce8)

class m00d4(fourbytes): 
    def __init__(self):
        super(m00d4, self).__init__(0x00d4, 0x00000000)

class m0197(fourbytes): 
    def __init__(self):
        super(m0197, self).__init__(0x0197, 0x00000003)

class m01a3(fourbytes): 
    def __init__(self):
        super(m01a3, self).__init__(0x01a3, 0x00000000)

class m020b(fourbytes): 
    def __init__(self):
        super(m020b, self).__init__(0x020b, 0x0001994b)

class m0219(fourbytes): 
    def __init__(self):
        super(m0219, self).__init__(0x0219, 0x00190c0c)

class m0225(fourbytes): 
    def __init__(self):
        super(m0225, self).__init__(0x0225, 0x00067675)

class m0228(fourbytes): 
    def __init__(self):
        super(m0228, self).__init__(0x0228, 0x00000000)

class m0259(fourbytes): 
    def __init__(self):
        super(m0259, self).__init__(0x0259, 0x00000000)

class m0296(fourbytes): 
    def __init__(self):
        super(m0296, self).__init__(0x0296, 0x00000007) # player level

class m0298(fourbytes): 
    def __init__(self):
        super(m0298, self).__init__(0x0298, 0x00000000)

class m0299(fourbytes): 
    def __init__(self):
        super(m0299, self).__init__(0x0299, 0x00000000)

class m02ab(fourbytes): 
    def __init__(self):
        super(m02ab, self).__init__(0x02ab, 0x00000000)

class m02b2(fourbytes): 
    def __init__(self):
        super(m02b2, self).__init__(0x02b2, 0x000005b0)

class m02b3(fourbytes): 
    def __init__(self):
        super(m02b3, self).__init__(0x02b3, 0x00001d06)

class m02b5(fourbytes): 
    def __init__(self):
        super(m02b5, self).__init__(0x02b5, 0x00866c82)

class m02be(fourbytes):
    def __init__(self):
        super(m02be, self).__init__(0x02be, 0x00000000)

class m02c4(fourbytes): 
    def __init__(self):
        super(m02c4, self).__init__(0x02c4, 0x0094883b)

class m02c7(fourbytes): 
    def __init__(self):
        super(m02c7, self).__init__(0x02c7, 0x00000000)

class m02d6(fourbytes): 
    def __init__(self):
        super(m02d6, self).__init__(0x02d6, 0x0000001c)

class m02d7(fourbytes): 
    def __init__(self):
        super(m02d7, self).__init__(0x02d7, 0x0000000E)

class m02d8(fourbytes): 
    def __init__(self):
        super(m02d8, self).__init__(0x02d8, 0x00000000) # unknown

class m02ec(fourbytes): 
    def __init__(self):
        super(m02ec, self).__init__(0x02ec, 0x00000004)

class m02ed(fourbytes): 
    def __init__(self):
        super(m02ed, self).__init__(0x02ed, 0x00000000)

class m02f4(fourbytes): 
    def __init__(self):
        super(m02f4, self).__init__(0x02f4, 0x000000a7)

class m02fc(fourbytes): 
    def __init__(self):
        super(m02fc, self).__init__(0x02fc, 0x00004949)

class m02ff(fourbytes): 
    def __init__(self):
        super(m02ff, self).__init__(0x02ff, 0x00000000)

class m0319(fourbytes): 
    def __init__(self):
        super(m0319, self).__init__(0x0319, 0x00000000)

class m0333(fourbytes): 
    def __init__(self):
        super(m0333, self).__init__(0x0333, 0x00000000)

class m0343(fourbytes): 
    def __init__(self):
        super(m0343, self).__init__(0x0343, 0x00000000)

class m0344(fourbytes): 
    def __init__(self):
        super(m0344, self).__init__(0x0344, 0x00000000)

class m0345(fourbytes): 
    def __init__(self):
        super(m0345, self).__init__(0x0345, 0x00000096)

class m0346(fourbytes): 
    def __init__(self):
        super(m0346, self).__init__(0x0346, 0x0000008c)

class m0347(fourbytes): 
    def __init__(self):
        super(m0347, self).__init__(0x0347, 0x00000000)

class m0348(fourbytes): 
    def __init__(self):
        super(m0348, self).__init__(0x0348, 0x0023a039)

class m0363(fourbytes): 
    def __init__(self):
        super(m0363, self).__init__(0x0363, 0x00000000)

class m0385(fourbytes): 
    def __init__(self):
        super(m0385, self).__init__(0x0385, 0x00002755)

class m03e0(fourbytes): 
    def __init__(self):
        super(m03e0, self).__init__(0x03e0, 0x00000000)

class m03f5(fourbytes): 
    def __init__(self):
        super(m03f5, self).__init__(0x03f5, 0x40000000)

class m03fd(fourbytes): 
    def __init__(self):
        super(m03fd, self).__init__(0x03fd, 0x00000000)

class m042a(fourbytes): 
    def __init__(self):
        super(m042a, self).__init__(0x042a, 0x00000007)

class m042b(fourbytes): 
    def __init__(self):
        super(m042b, self).__init__(0x042b, 0x00004782)

class m042e(fourbytes): 
    def __init__(self):
        super(m042e, self).__init__(0x042e, 0x42700000)

class m042f(fourbytes): 
    def __init__(self):
        super(m042f, self).__init__(0x042f, 0x41a00000)

class m0448(fourbytes):
    def __init__(self):
        super(m0448, self).__init__(0x0448, 0x00000000)

class m0452(fourbytes): 
    def __init__(self):
        super(m0452, self).__init__(0x0452, 0x00000001)

class m0489(fourbytes): 
    def __init__(self):
        super(m0489, self).__init__(0x0489, 0x00000000)

class m049e(fourbytes): 
    def __init__(self):
        super(m049e, self).__init__(0x049e, 0x01040B61)

class m04cb(fourbytes): 
    def __init__(self):
        super(m04cb, self).__init__(0x04cb, 0x00100000) # xp

class m0502(fourbytes): 
    def __init__(self):
        super(m0502, self).__init__(0x0502, 0x00000000)

class m0556(fourbytes): 
    def __init__(self):
        super(m0556, self).__init__(0x0556, 0x00000000)

class m0558(fourbytes): 
    def __init__(self):
        super(m0558, self).__init__(0x0558, 0x00000000)

class m058a(fourbytes): 
    def __init__(self):
        super(m058a, self).__init__(0x058a, 0x00000000)

class m05cf(fourbytes): 
    def __init__(self):
        super(m05cf, self).__init__(0x05cf, 0x00000000)

class m05d3(fourbytes): 
    def __init__(self):
        super(m05d3, self).__init__(0x05d3, 0x00001000) # gold

class m05dc(fourbytes): 
    def __init__(self):
        super(m05dc, self).__init__(0x05dc, 0x00050000)

class m05e9(fourbytes): 
    def __init__(self):
        super(m05e9, self).__init__(0x05e9, 0x00000000)

class m060a(fourbytes): 
    def __init__(self):
        super(m060a, self).__init__(0x060a, 0x7b19f822)

class m060c(fourbytes): 
    def __init__(self):
        super(m060c, self).__init__(0x060c, 0x00000000) 

class m0615(fourbytes): 
    def __init__(self):
        super(m0615, self).__init__(0x0615, 0x00000000) 

class m0623(fourbytes): 
    def __init__(self):
        super(m0623, self).__init__(0x0623, 0x00000000)

class m062d(fourbytes): 
    def __init__(self):
        super(m062d, self).__init__(0x062d, 0x00060001)

class m062e(fourbytes): 
    def __init__(self):
        super(m062e, self).__init__(0x062e, 0x00000000)

class m062f(fourbytes): 
    def __init__(self):
        super(m062f, self).__init__(0x062f, 0x00000000)

class m0661(fourbytes): 
    def __init__(self):
        super(m0661, self).__init__(0x0661, 0x00000000)

class m0663(fourbytes): 
    def __init__(self):
        super(m0663, self).__init__(0x0663, 0x00050001)

class m0664(fourbytes): 
    def __init__(self):
        super(m0664, self).__init__(0x0664, 0x00044107)

class m0671(fourbytes):
    def __init__(self):
        super(m0671, self).__init__(0x0671, 0x00000000)

class m0672(fourbytes):
    def __init__(self):
        super(m0672, self).__init__(0x0672, 0x00000000)

class m0674(fourbytes):
    def __init__(self):
        super(m0674, self).__init__(0x0674, 0x00000000)

class m0675(fourbytes):
    def __init__(self):
        super(m0675, self).__init__(0x0675, 0x00000000)

class m0676(fourbytes):
    def __init__(self):
        super(m0676, self).__init__(0x0676, 0x00000000)

class m0677(fourbytes):
    def __init__(self):
        super(m0677, self).__init__(0x0677, 0x00000000)

class m06bd(fourbytes): 
    def __init__(self): 
        super(m06bd, self).__init__(0x06bd, 0x0000001e) 

class m06bf(fourbytes): 
    def __init__(self): 
        super(m06bf, self).__init__(0x06bf, 0x00000032) 

class m06ea(fourbytes): 
    def __init__(self): 
        super(m06ea, self).__init__(0x06ea, 0x00000000) 

class m06ee(fourbytes): 
    def __init__(self): 
        super(m06ee, self).__init__(0x06ee, 0x00000000)

class m06f1(fourbytes): 
    def __init__(self): 
        super(m06f1, self).__init__(0x06f1, 0x41700000)

class m06f5(fourbytes): 
    def __init__(self): 
        super(m06f5, self).__init__(0x06f5, 0x00000000)

class m0701(fourbytes): 
    def __init__(self): 
        super(m0701, self).__init__(0x0701, 0x00000000)

#------------------------------------------------------------
# nbytes
#------------------------------------------------------------
class m0008(nbytes):
    def __init__(self):
        super(m0008, self).__init__(0x0008, hexparse('00 00 00 00 00 00 00 00'))

class m00b7(nbytes):
    def __init__(self):
        super(m00b7, self).__init__(0x00b7, hexparse('d0 69 03 1d f9 4c e4 40'))

class m01d7(nbytes):
    def __init__(self):
        super(m01d7, self).__init__(0x01d7, hexparse('00 00 00 00 2c 20 e5 40'))

class m0246(nbytes):
    def __init__(self):
        super(m0246, self).__init__(0x0246, hexparse('00 00 00 00 00 00 00 00'))

    def set(self, ip1, ip2, ip3, ip4, port):
        self.value = struct.pack('>BBHBBBB', 0x02, 0x00, port, ip1, ip2, ip3, ip4)
        return self

class m024f(nbytes):
    def __init__(self):
        super(m024f, self).__init__(0x024f, hexparse('00 00 00 00 00 00 00 00'))

    def set(self, ip1, ip2, ip3, ip4, port):
        self.value = struct.pack('>BBHBBBB', 0x02, 0x00, port, ip1, ip2, ip3, ip4)
        return self

class m0303(nbytes):
    def __init__(self):
        super(m0303, self).__init__(0x0303, hexparse('00 00 00 40 00 00 00 00'))

class m03e3(nbytes):
    def __init__(self):
        super(m03e3, self).__init__(0x03e3, 
                hexparse('00 00 00 00 00 00 00 00 '
                         '00 00 00 00 00 00 00 00'))
                #hexparse('6b 6a 0a 5f 8f 04 e7 41 '
                #         '81 96 29 0b 80 49 83 cf'))

class m0419(nbytes):
    def __init__(self):
        super(m0419, self).__init__(0x0419, hexparse('00 00 00 00 0c 20 e5 40'))

class m0434(nbytes):
    def __init__(self):
        super(m0434, self).__init__(0x0434, hexparse('03 4c ba fa 2e 26 40 01'))

class m05e4(nbytes):
    def __init__(self):
        super(m05e4, self).__init__(0x05e4, hexparse('00 00 00 00 00 00 00 00'))

#------------------------------------------------------------
# stringenums
#------------------------------------------------------------

class m0013(stringenum):
    def __init__(self):
        super(m0013, self).__init__(0x0013, 'y')

class m00a3(stringenum):
    def __init__(self):
        super(m00a3, self).__init__(0x00a3, '')

class m00aa(stringenum):
    def __init__(self):
        super(m00aa, self).__init__(0x00aa, 'y')

class m01a4(stringenum):
    def __init__(self):
        super(m01a4, self).__init__(0x01a4, '')

class m01a6(stringenum):
    def __init__(self):
        super(m01a6, self).__init__(0x01a6, 'n')

class m01bc(stringenum):
    def __init__(self):
        super(m01bc, self).__init__(0x01bc, 'n')

class m01c4(stringenum):
    def __init__(self):
        super(m01c4, self).__init__(0x01c4, 'n')

class m02af(stringenum):
    def __init__(self):
        super(m02af, self).__init__(0x02af, 'n')

class m02b1(stringenum):
    def __init__(self):
        super(m02b1, self).__init__(0x02b1, '')

class m02b6(stringenum):
    def __init__(self):
        super(m02b6, self).__init__(0x02b6, '')

class m02e6(stringenum):
    def __init__(self):
        super(m02e6, self).__init__(0x02e6, '')

class m02fe(stringenum):
    def __init__(self):
        super(m02fe, self).__init__(0x02fe, '')

class m0300(stringenum):
    def __init__(self):
        super(m0300, self).__init__(0x0300, '')

class m034a(stringenum):
    def __init__(self):
        super(m034a, self).__init__(0x034a, '')

class m035b(stringenum):
    def __init__(self):
        super(m035b, self).__init__(0x035b, 'y')

class m037c(stringenum):
    def __init__(self):
        super(m037c, self).__init__(0x037c, 'n')

class m0468(stringenum):
    def __init__(self):
        super(m0468, self).__init__(0x0468, 'f8')

class m0494(stringenum):
    def __init__(self):
        super(m0494, self).__init__(0x0494, '')

class m0669(stringenum):
    def __init__(self):
        super(m0669, self).__init__(0x0669, '')

class m06de(stringenum):
    def __init__(self):
        super(m06de, self).__init__(0x06de, '')

class m06e9(stringenum):
    def __init__(self):
        super(m06e9, self).__init__(0x06e9, 'n')

#------------------------------------------------------------
# arrayofenumblockarrays
#------------------------------------------------------------

class m00e9(arrayofenumblockarrays):
    def __init__(self):
        super(m00e9, self).__init__(0x00e9)
        self.arrays = [
            [
                m0385(),
                m06ee(),
                m02c7().set(0x431c),
                m0008(),
                m02ff(),
                m02ed(),
                m02d8(),
                m02ec(),
                m02d7(),
                m02af(),
                m0013(),
                m00aa(),
                m01a6(),
                m06f1(),
                m0703(),
                m0343(),
                m0344(),
                m0259(),
                m03fd(),
                m02b3(),
                m0448().set(4),
                m02d6(),
                m06f5(),
                m0299(),
                m0298(),
                m06bf(),
                m069c(),
                m069b(),
                m0300().set('DarkServe'),
                m01a4().set('CTF fun, no *****ers :)'),
                m02b2(),
                m02b5(),
                m0347().set(0x00000018),
                m02f4(),
                m0035(),
                m0197(),
                m0246().set(10,0,0,1,1234)
            ]
        ]

class m00fe(arrayofenumblockarrays):
    def __init__(self):
        super(m00fe, self).__init__(0x00fe)

    def write(self, stream):
        stream.write(_originalbytes(0x8519, 0x873d))

class m0138(arrayofenumblockarrays):
    def __init__(self):
        super(m0138, self).__init__(0x0138)

    #def write(self, stream):
    #    stream.write(_originalbytes(0x103, 0x4f49))

class m0144(arrayofenumblockarrays):
    def __init__(self):
        super(m0144, self).__init__(0x0144)
        
class m06ef(arrayofenumblockarrays):
    def __init__(self):
        super(m06ef, self).__init__(0x06ef)
        self.arrays = [
            [
                m06ee(),
                m042e(),
                m042f(),
                m03f5()
            ],
            [
                m06ee(),
                m042e(),
                m042f(),
                m03f5()
            ]
        ]

class m0632(arrayofenumblockarrays):
    def __init__(self):
        super(m0632, self).__init__(0x0632)

    def write(self, stream):
        stream.write(_originalbytes(0x7371, 0x8515))

class m0633(arrayofenumblockarrays):
    def __init__(self):
        super(m0633, self).__init__(0x0633)

    def write(self, stream):
        stream.write(_originalbytes(0xdaff, 0x19116))

class m063e(arrayofenumblockarrays):
    def __init__(self):
        super(m063e, self).__init__(0x063e)

    def write(self, stream):
        stream.write(_originalbytes(0x19116, 0x1c6ee))

class m0662(arrayofenumblockarrays):
    def __init__(self, start, end):
        super(m0662, self).__init__(0x0662)
        self.start = start
        self.end = end

    def write(self, stream):
        stream.write(_originalbytes(self.start, self.end))

class m067e(arrayofenumblockarrays):
    def __init__(self):
        super(m067e, self).__init__(0x067e)

    def write(self, stream):
        stream.write(_originalbytes(0x1c6ee, 0x1ec45))

class m0681(arrayofenumblockarrays):
    def __init__(self):
        super(m0681, self).__init__(0x0681)

class m068b(arrayofenumblockarrays):
    def __init__(self):
        super(m068b, self).__init__(0x068b)
        self.arrays = [
            [
                m0448().set(4),
                m03fd(),
                m06e9(),
                m02ff(),
                m0300().set("Europe"),
                m0246().set(10, 0, 0, 1, 1234)
            ]
        ]    

class m0681(arrayofenumblockarrays):
    def __init__(self):
        super(m0681, self).__init__(0x0681)

    def write(self, stream):
        stream.write(_originalbytes(0x8822, 0x8898))

#------------------------------------------------------------
# enumblockarrays
#------------------------------------------------------------

class a0014(enumblockarray):
    def __init__(self):
        super(a0014, self).__init__(0x0014)

class a0033(enumblockarray):
    def __init__(self):
        super(a0033, self).__init__(0x0033)

class a0035(enumblockarray):
    def __init__(self):
        super(a0035, self).__init__(0x0035)
        self.content = [
                m0348(),
                m0095(),
                m02c7().set(0x431c),
                m06ee(),
                m02c4(),
                m02b2(),
                m037c(),
                m0452(),
                m0225(),
                m0363(),
                m0615(),
                m06ef(),
                m024f().set(127,0,0,1,7777),
                m0246().set(10,0,0,1,1234),
                m0448().set(4),
                m02b5(),
                m03e0(),
                m0347().set(7),
                m060a(),
                m02be().set(0x0000034f),
                m02b1().set('TrCTF-ArxNovena'),
                m00a3().set('TribesGame.TrGame_TRCTF'),
                m0326(),
                m0600(),
                m02ff(),
            m01a3(),
            m020b(),
            m0345(),
            m0346(),
            m02d8()
        ]

class a003a(enumblockarray):
    def __init__(self):
        super(a003a, self).__init__(0x003a)
        self.content = [
                m049e(),
                m03e3(),
                m0434()
        ]

class a003d(enumblockarray):
    def __init__(self):
        super(a003d, self).__init__(0x003d)
        self.content = [
            m03e3(),
            m0348(),
            m0095(),
            m034a().set('Griffon28'),
            m06de().set('tag'),
            m0303(),
            m0296(),
            m05dc(),
            m04cb(),
            m0701(),
            m05d3(),
            m00d4(),
            m0502(),
            m0448().set(4),
            m05e9(),
            m060c(),
            m05e4(),
            m06ea(),
            m058a(),
            m02be().set(0x00000000),
            m0138(),
            m0662(0x4f49, 0x7371),
            m0632(),
            m0681(),
            m00fe(),
            m062d(),
            m008d(),
            m062e(),
            m0419(),
            m01d7(),
            m00b7(),
            m062f(),
            m01bc(),
            m0468(),
            m0663(),
            m068b(),
            m0681()]

class a0041(enumblockarray):
    def __init__(self):
        super(a0041, self).__init__(0x0041)

class a004c(enumblockarray):
    def __init__(self):
        super(a004c, self).__init__(0x004c)

class a006d(enumblockarray):
    def __init__(self):
        super(a006d, self).__init__(0x006d)

class a006f(enumblockarray):
    def __init__(self):
        super(a006f, self).__init__(0x006f)

class a0070(enumblockarray):
    def __init__(self):
        super(a0070, self).__init__(0x0070)

class a0070(enumblockarray):
    def __init__(self):
        super(a0070, self).__init__(0x0070)

class a0085(enumblockarray):
    def __init__(self):
        super(a0085, self).__init__(0x0085)

class a00b0(enumblockarray):
    def __init__(self, length):
        super(a00b0, self).__init__(0x00b0)
        self.content = [
            m035b(),
            m0348(),
            m042a(),
            m0558(),
            m02c7().set(0x431c),
            m0333()
        ]
        if length == 9:
            self.content.extend([
                m02ff(),
                m06ee(),
                m042b()
            ])
        else:
            self.content.extend([
                m02c4(),
                m06ee(),
                m0452(),
                m0225()
            ])

class a00b1(enumblockarray):
    def __init__(self):
        super(a00b1, self).__init__(0x00b1)

class a00b2(enumblockarray):
    def __init__(self):
        super(a00b2, self).__init__(0x00b2)

class a00b3(enumblockarray):
    def __init__(self):
        super(a00b3, self).__init__(0x00b3)

class a00b4(enumblockarray):
    def __init__(self):
        super(a00b4, self).__init__(0x00b4)
        self.content = [
            m042b(),
            m01c4(),
            m0556(),
            m035b(),
            m0348(),
            m042a(),
            m0558(),
            m02c7().set(0),
            m0333(),
            m06bd(),
            m02c4(),
            m06ee(),
            m0452(),
            m0225()
        ]

class a00d5(enumblockarray):
    def __init__(self):
        super(a00d5, self).__init__(0x00d5)
        self.content = [
            m0228().set(2),
            m00e9(),
            m0347().set(0x2f6b9f)
        ]

class a011c(enumblockarray):
    def __init__(self):
        super(a011c, self).__init__(0x011c)

class a0175(enumblockarray):
    def __init__(self):
        super(a0175, self).__init__(0x0175)
        
class a0176(enumblockarray):
    def __init__(self):
        super(a0176, self).__init__(0x0176)

class a0177(enumblockarray):
    def __init__(self):
        super(a0177, self).__init__(0x0177)

class a0182(enumblockarray):
    def __init__(self):
        super(a0182, self).__init__(0x0182)

class a0183(enumblockarray):
    def __init__(self):
        super(a0183, self).__init__(0x0183)

class a018b(enumblockarray):
    def __init__(self):
        super(a018b, self).__init__(0x018b)

class a0197(enumblockarray):
    def __init__(self):
        super(a0197, self).__init__(0x0197)
        self.content = [
            m0664(),
            m03e3(),
            m03e0()
        ]

class a01b5(enumblockarray):
    def __init__(self):
        super(a01b5, self).__init__(0x01b5)

class a01bc(enumblockarray):
    def __init__(self):
        super(a01bc, self).__init__(0x01bc)
        self.content = [
            m049e(),
            m0489().set(0x0000000c),
            m0319()
        ]

class a01c6(enumblockarray):
    def __init__(self):
        super(a01c6, self).__init__(0x01c6)

class a01c8(enumblockarray):
    def __init__(self):
        super(a01c8, self).__init__(0x01c8)

#------------------------------------------------------------
# special fields
#------------------------------------------------------------

class m0056():
    def __init__(self):
        self.ident = 0x0056
        self.content = b'0' * 90

    def write(self, stream):
        stream.write(struct.pack('<HL', self.ident, len(self.content)) + self.content)

    def read(self, stream):
        ident, length = struct.unpack('<HL', stream.read(6))
        if ident != self.ident:
            raise ParseError('self.ident(%02X) did not match parsed ident value (%02X)' % (self.ident, ident))
        self.content = stream.read(length)
        return self

class originalfragment():
    def __init__(self, fromoffset, tooffset):
        self.fromoffset = fromoffset
        self.tooffset = tooffset

    def write(self, stream):
        stream.write(_originalbytes(self.fromoffset, self.tooffset))


def constructenumblockarray(stream):
    ident = struct.unpack('<H', stream.peek(2))[0]
    classname = ('a%04X' % ident).lower()
    print('constructing %s' % classname)
    obj = globals()[classname]().read(stream)
    return obj

