#!/usr/bin/python

class instruction:
	ifetch = False
	idec = False
	execute = False
	wb = False
	def __init__(self, code, label, raw, war, waw):
		#The label fieled will contain one if the first element is a label
		self.ifetch = False
		self.idec = False
		self.execute = False
		self.wb = False
		self.label = label
		self.raw = raw
		self.war = war
		self.waw = waw

		
