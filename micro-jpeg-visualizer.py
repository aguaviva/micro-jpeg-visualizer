#!/usr/bin/env python
# Written by Raul Aguaviva as an exercise
# beware not optimized for speed or clarity :-)

from struct import *
import math 

zigzag = [0,  1,  8, 16,  9,  2,  3, 10,
	17, 24, 32, 25, 18, 11,  4,  5,
	12, 19,	26, 33, 40, 48, 41, 34,
	27, 20, 13,  6,  7, 14, 21, 28,
	35, 42, 49, 56, 57, 50, 43, 36,
	29, 22, 15, 23, 30, 37, 44, 51,
	58, 59, 52, 45, 38, 31, 39, 46,
	53, 60, 61, 54, 47, 55, 62, 63]

def Clamp(col):
	col = 255 if col>255 else col
	col = 0 if col<0 else col
	return  int(col)

def HexDump(data):
	for i in range(len(data)):
		b, = unpack("B",data[i:i+1])		
		print("%02x " % b),

def ColorConversion(Y, Cr, Cb):
	R = Cr*(2-2*.299) + Y
	B = Cb*(2-2*.114) + Y
	G = (Y - .114*B - .299*R)/.587
	return (Clamp(R+128),Clamp(G+128),Clamp(B+128) )

def GetArray(type,l, length):
	s = ""
	for i in range(length):
		s =s+type
	return list(unpack(s,l[:length]))


def DecodeNumber(code, bits):
	l = 2**(code-1)
	if bits>=l:
		return bits
	else:
		return bits-(2*l-1)
	
def PrintMatrix( m):
	for j in range(8):
		for i in range(8):
			print("%2f" % m[i+j*8]),
		print
	print

def XYtoLin(x,y):
	return x+y*8

def DrawMatrix(x, y, matL, matCb,matCr):
	for yy in range(8):
		for xx in range(8):
			c = "#%02x%02x%02x" % ColorConversion( matL[XYtoLin(xx,yy)] , matCb[XYtoLin(xx,yy)], matCr[XYtoLin(xx,yy)])
			w.create_rectangle((x*8+xx)*2, (y*8+yy)*2, (x*8+(xx+1))*2, (y*8+(yy+1))*2, fill=c,outline= c)

def RemoveFF00(data):
	datapro = []
	i = 0
	while(True):
		b,bnext = unpack("BB",data[i:i+2])		
		if (b == 0xff):
			if (bnext != 0):
				break
			datapro.append(data[i])
			i+=2
		else:
			datapro.append(data[i])
			i+=1
	return datapro,i

# helps build a MCU matrix
class IDCT:
	def __init__(self):
		self.base = [0]*64

	def NormCoeff(self, n):
		return math.sqrt( 1.0/8.0) if (n==0) else math.sqrt( 2.0/8.0)

	def AddIDC(self, n,m, coeff):
		an = self.NormCoeff(n)
		am = self.NormCoeff(m)
				
		for y in range(0,8):			
			for x in range(0,8):
				nn = an*math.cos( n* math.pi * (x +.5)/8.0 )
				mm = am*math.cos( m* math.pi * (y +.5)/8.0 )
				self.base[ XYtoLin(x, y) ] += nn*mm*coeff

	def AddZigZag(self, zi, coeff):
		i = zigzag[zi]
		n = i & 0x7
		m = i >> 3
		self.AddIDC( n,m, coeff)

# convert a string into a bit stream
class Stream:
	def __init__(self, data):
		self.data= data
		self.pos = 0

	def GetBit(self):
		b = ord(self.data[self.pos >> 3])
		s = 7-(self.pos & 0x7)
		self.pos+=1
		return (b >> s) & 1

	def GetBitN(self, l):
		val = 0
		for i in range(l):
			val = val*2 + self.GetBit()
		return val

# Create huffman bits from table lengths
class HuffmanTable:
	def __init__(self):
		self.root=[]
		self.elements = []
	
	def BitsFromLengths(self, root, element, pos):
		if isinstance(root,list):
			if pos==0:
				if len(root)<2:
					root.append(element)
					return True				
				return False
			for i in [0,1]:
				if len(root) == i:
					root.append([])
				if self.BitsFromLengths(root[i], element, pos-1) == True:
					return True
		return False
	
	def GetHuffmanBits(self,  lengths, elements):
		self.elements = elements
		ii = 0
		for i in range(len(lengths)):
			for j in range(lengths[i]):
				self.BitsFromLengths(self.root, elements[ii], i)
				ii+=1

	def Find(self,st):
		r = self.root
		while isinstance(r, list):
			r=r[st.GetBit()]
		return  r 

	def GetCode(self, st):
		while(True):
			res = self.Find(st)
			if res == 0:
				return 0
			elif ( res != -1):
				return res

# main class that decodes the jpeg
class jpeg:
	def __init__(self):
		self.quant = {}
		self.quantMapping = []
		self.tables = {}
		self.width = 0
		self.height = 0

	def BuildMatrix(self, st, idx, quant, olddccoeff):	
		i = IDCT()	
		code = self.tables[0+idx].GetCode(st)
		bits = st.GetBitN(code)
		dccoeff = DecodeNumber(code, bits)  + olddccoeff

		i.AddZigZag(0,(dccoeff) * quant[0])
		l = 1
		while(l<64):
			code = self.tables[16+idx].GetCode(st) 
			if code == 0:
				break
			if code >15:
				l+= (code>>4)
				code = code & 0xf	
			
			bits = st.GetBitN( code )

			if l<64:						
				coeff  =  DecodeNumber(code, bits) 
				i.AddZigZag(l,coeff * quant[l])
				l+=1
		return i,dccoeff
	
	def StartOfScan(self, data, hdrlen):
		data,lenchunk = RemoveFF00(data[hdrlen:])

		st = Stream(data)

		oldlumdccoeff, oldCbdccoeff, oldCrdccoeff = 0, 0, 0
		for y in range(self.height//8):
			for x in range(self.width//8):
				#print "MCU:", x,y
				matL, oldlumdccoeff = self.BuildMatrix(st,0, self.quant[self.quantMapping[0]], oldlumdccoeff)
				matCr, oldCrdccoeff = self.BuildMatrix(st,1, self.quant[self.quantMapping[1]], oldCrdccoeff)
				matCb, oldCbdccoeff = self.BuildMatrix(st,1, self.quant[self.quantMapping[2]], oldCbdccoeff)
				DrawMatrix(x, y, matL.base, matCb.base, matCr.base )	
				#PrintMatrix(matL.base)
		
		return lenchunk +hdrlen

	def DefineQuantizationTables(self, data):
		while(len(data)>0):
			hdr, = unpack("B",data[0:1])
			#print hdr >>4, hdr & 0xf
			self.quant[hdr & 0xf] =  GetArray("B", data[1:1+64],64)
			#PrintMatrix(self.quant[hdr >>4])
			data = data[65:]

	def BaselineDCT(self, data):
		hdr, self.height, self.width, components = unpack(">BHHB",data[0:6])
		print("size %ix%i" % (self.width,  self.height))

		for i in range(components):
			id, samp, QtbId = unpack("BBB",data[6+i*3:9+i*3])
			self.quantMapping.append(QtbId) 		
		
	def DefineHuffmanTables(self, data):
		while(len(data)>0):
			off = 0
			hdr, = unpack("B",data[off:off+1])
			off+=1
			#print hdr	

			lengths = GetArray("B", data[off:off+16],16) 
			off += 16
		
			elements = []
			for i in lengths:
				elements+= (GetArray("B", data[off:off+i], i))
				off = off+i 

			hf = HuffmanTable()
			hf.GetHuffmanBits( lengths, elements)
			self.tables[hdr] = hf

			data = data[off:]

	def decode(self, data):	
		while(True):
			hdr, = unpack(">H", data[0:2])
			if hdr == 0xffd8:
				lenchunk = 2
			elif hdr == 0xffd9:
				return
			else:
				lenchunk, = unpack(">H", data[2:4])
				lenchunk+=2
				chunk = data[4:lenchunk]
				if hdr == 0xffdb:
					self.DefineQuantizationTables(chunk)
				elif hdr == 0xffc0:
					self.BaselineDCT(chunk)
				elif hdr == 0xffc4:
					self.DefineHuffmanTables(chunk)
				elif hdr == 0xffda:
					lenchunk = self.StartOfScan(data, lenchunk)
			
			data = data[lenchunk:]
			if len(data)==0:
				break		

from tkinter import *
master = Tk()
w = Canvas(master, width=1600, height=600)
w.pack()

#jpeg().decode(open('images/huff_simple0.jpg', 'rb').read())
#jpeg().decode(open('images/surfer.jpg', 'rb').read())
jpeg().decode(open('images/porsche.jpg', 'rb').read())
mainloop()