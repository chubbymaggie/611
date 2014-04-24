#!/usr/bin/python
import sys
import mips_parser
import destination_op_finder
import raw_finder
import waw_finder
import war_finder


#LOGICS FOR LW AND SW ARE YET TO BE IMPLEMENTED. 
#LOGICS FOR SOME ARITHMENATIC OPERATIONS MIGHT NOT BE IMPLEMENTED.
#WRITEBACK PRIORITY HAS NOT BEEN IMPLEMENTED. 
#SELF.LINE_OF_CODE CAN BE USED AS ADDRESS NUMBER. 

obj_list = []
class configuration:
	def __init__(self, fpadder, fpmult, fpdiv, mem, icac, dcac):
		self.fpadder = fpadder #set latency of floating point adder
		self.fpmult = fpmult   #set latency of floating point multiplier
		self.fpdiv  = fpdiv	#set latency of floating point divider
		self.mem = mem		#set latency of data memory
		self.icac = icac	#set latency of cache memory
		self.dcac = dcac	#set latency of data memory
	
	def set_pipelines(self, fpa, fpm, fpd):
		self.pipe_fpa = fpa # True if the unit is pipelined
		self.pipe_fpm = fpm #True if the unit is pipelined
		self.pipe_fpd = fpd #True if the unit is pipelined
	
	def printconf(self):
		print self.pipe_fpa
		print self.pipe_fpm
		print self.pipe_fpd
		print self.fpadder
		print self.fpmult
		print self.fpdiv
		print self.mem
		print self.icac
		print self.dcac
	




class instruction:	
	mainif_busy = False
	mainid_busy = False
	mainui_busy = False
	mainadd_busy = False
	main_add_pipe = None
	main_add_latency = 1
	mainmul_busy = False
	mainmul_pipe = None
	mainmul_latency = 1
	maindiv_busy = False
	maindiv_pipe = None
	maindiv_latency = 1
	mainmemory_latency = 1
	icache_latency = 1
	dcache_latency = 1
	ifsetter = 0
	idsetter = 0
	uisetter = 0
	addsetter = 0
	mulsetter = 0
	divsetter = 0
	mainwb_busy = False
	wbsetter = 0
	databussetter = 0
	label_dictionary = None
	maindatabus_busy = False
	ref_objlist = []
	registers = []
	memdata = []

	def __init__(self, code, raw_list, war_list, waw_list, dest, line_of_code):
		self.line_of_code = line_of_code
		self.raw = [] if raw_list is None else raw_list
		self.war = [] if war_list is None else war_list
		self.waw = [] if waw_list is None else waw_list
		self.dest = dest
		self.code = code
		self.hideme = 0
		self.result = [None, None, None, None]
		self.hazards = ["N", "N", "N", "N"]
		self.ifstage = False
		self.setiffalse = 0
		self.idstage = False
		self.setidfalse = False
		self.execstage = False
		self.wbstage = False
		self.setwbfalse = 0
		self.uidone = False
		self.setuifalse = 0
		self.memdone = False
		self.setaddfalse = 0
		self.setdivfalse = 0
		self.setmulfalse = 0
		self.setdatabusfalse = 0
		self.fpa = False
		self.fpm = False
		self.fpd = False
		self.fpalatency = instruction.main_add_latency	
		self.fpdlatency = instruction.maindiv_latency
		self.fpmlatency = instruction.mainmul_latency
		self.lwcounter = instruction.dcache_latency
		self.ldcounter = 2 * instruction.dcache_latency
	
	def action(self, num, counter):
		global obj_list
		#"""WRITING THE IF STAGE FUNCTIONALITY HERE"""
		if(self.ifstage == False):
			if((instruction.mainif_busy == False) and ((num == 0) or (obj_list[num - 1].idstage == True))):
				instruction.mainif_busy = True
				instruction.ifsetter = num
				self.setiffalse = 1
				self.ifstage = True
			else:
				pass


		#"""WRITING THE ID STAGE FUNCTIONALITY HERE"""
		
		elif((self.ifstage == True) and (self.idstage == False)):
			if((instruction.mainid_busy == False) or (instruction.mainid_busy == True and instruction.idsetter == num)):
				if instruction.mainid_busy == False:
					self.result[0] = counter - 1
				instruction.mainid_busy = True
				instruction.idsetter = num
				flagraw = 0
				flagwaw = 0
				self.hazards[1] == "N"
				for elements in self.raw:
					diff = self.line_of_code - elements
					if obj_list[num - diff].wbstage == False:
						flagraw = 1
						self.hazards[0] = "Y"
				for elements in self.waw:
					diff = self.line_of_code - elements
					if obj_list[num - diff].wbstage == False:
						flagwaw = 1
						self.hazards[2] = "Y"
				if flagraw == 1 or flagwaw == 1:
					pass
				elif flagraw == 0 and flagwaw == 0:
					self.setidfalse = 1
					self.idstage = True
				#Because the Jump instruction actually needs to end at the ID Stage
				if self.idstage == True:
					if self.code[0] == "j":
						try:
							jumper = instruction.label_dictionary[self.code[1]]
						except:
							print "Your label dictionary is really wronf man"
							sys.exit(1)
						if jumper > self.line_of_code and jumper != None:
							diff = jumper - self.line_of_code
							for stuff in range(num , num + diff):
								obj_list[stuff].hideme = 1
								obj_list[stuff].ifstage = True
								obj_list[stuff].idstage = True
								obj_list[stuff].execstage = True
								obj_list[stuff].wbstage = True
							#Also Just write the result in the IF Stage of the next hidden statement
							self.result[1] = counter
							obj_list[num + 1].result[0] = counter
							instruction.ifsetter = num + 1
							obj_list[num + 1].setiffalse = 1
						elif jumper < self.line_of_code and jumper != None:
							for stuff in range(num, len(obj_list)):
								obj_list[stuff].hideme = 1
								obj_list[stuff].ifstage = True
								obj_list[stuff].idstage = True
								obj_list[stuff].execstage = True
								obj_list[stuff].wbstage = True
							#Also Just write the result in the IF Stage of the next hidden statement
							self.result[1] = counter
							obj_list[num + 1].result[0] = counter
							instruction.ifsetter = num + 1
							obj_list[num + 1].setiffalse = 1
							#THIS LINE IS EXTREMELY IMPORTANT.
							obj_list.extend(instruction.ref_objlist[jumper:])
					elif self.code[0] == "hlt":
						self.hideme = 1
						self.result[1] = counter
						obj_list[num + 1].hideme = 1
						obj_list[num + 1].result[0] = counter	
						instruction.ifsetter = num + 1
						obj_list[num + 1].setiffalse = 1

					elif self.code[0] == "bne":
						if int(instruction.registers[int(self.code[1][1:])], 2) != int(instruction.registers[int(self.code[2][1:])], 2):
							try:
								jumper = instruction.label_dictionary[self.code[3]]
							except:
								print "Error with the label dictionary"
							if jumper > self.line_of_code and jumper != None:
								diff = jumper - self.line_of_code
								for stuff in range(num, num + diff):
									obj_list[stuff].hideme = 1
									obj_list[stuff].ifstage = True
									obj_list[stuff].idstage = True
									obj_list[stuff].execstage = True
									obj_list[stuff].wbstage = True
								self.result[1] = counter
								obj_list[num + 1].result[0] = counter
								instruction.ifsetter = num + 1
								obj_list[num + 1].setiffalse = 1
							elif jumper < self.line_of_code and jumper != None:
								for stuff in range(num, len(obj_list)):
									obj_list[stuff].hideme = 1
									obj_list[stuff].ifstage = True
									obj_list[stuff].idstage = True
									obj_list[stuff].execstage = True
									obj_list[stuff].wbstage = True
								self.result[1] = counter
								obj_list[num + 1].result[0] = counter
								instruction.ifsetter = num + 1
								obj_list[num + 1].setiffalse = 1	
								#THIS LINE IS EXTREMELY IMPORTANT.
								obj_list.extend(instruction.ref_objlist[jumper:])
						else:
							self.result[1] = counter				

					elif self.code[0] == "beq":
						if int(instruction.registers[int(self.code[1][1:])], 2) == int(instruction.registers[int(self.code[2][1:])], 2):
							try:
								jumper = instruction.label_dictionary[self.code[3]]
							except:
								print "Error with the label dictionary"
							if jumper > self.line_of_code and jumper != None:
								diff = jumper - self.line_of_code
								for stuff in range(num, num + diff):
									obj_list[stuff].hideme = 1
									obj_list[stuff].ifstage = True
									obj_list[stuff].idstage = True
									obj_list[stuff].execstage = True
									obj_list[stuff].wbstage = True
								self.result[1] = counter
								obj_list[num + 1].result[0] = counter
								instruction.ifsetter = num + 1
								obj_list[num + 1].setiffalse = 1
							elif jumper < self.line_of_code and jumper != None:
								for stuff in range(num, len(obj_list)):
									obj_list[stuff].hideme = 1
									obj_list[stuff].ifstage = True
									obj_list[stuff].idstage = True
									obj_list[stuff].execstage = True
									obj_list[stuff].wbstage = True
								self.result[1] = counter
								obj_list[num + 1].result[0] = counter
								instruction.ifsetter = num + 1
								obj_list[num + 1].setiffalse = 1	
								#THIS LINE IS EXTREMELY IMPORTANT.
								obj_list.extend(instruction.ref_objlist[jumper:])
						else:
							self.result[1] = counter
			#DETECTING A STRUCTURAL HAZARD				
			elif instruction.mainid_busy == True and instruction.idsetter != num:
				self.hazards[3] = "Y"		
		
		#Writing the code for the exec stage
		elif (self.idstage == True) and (self.execstage == False):
			#EXEC INSTRUCTIONS FOR LOAD WORD
			if self.code[0] == "lw":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False) or (self.uidone == True and instruction.maindatabus_busy == True 
					and instruction.databussetter == num and self.memdone == False)):

					instruction.maindatabus_busy = True
					instruction.databussetter = num
					self.lwcounter = self.lwcounter - 1
					if self.lwcounter == 0:
						self.execstage = True
						self.setdatabusfalse = 1
						"""LOAD WORD ACTUAL LOGIC NEEDED"""
						#lw r1 4(r2)
						#lw r1 r2
						if "(" in self.code[2]:
							number = int(self.code[2][0]) + int(instruction.registers[int(self.code[2][-2])], 2)
							"""ACTUAL LOAD LOGIC CONTINUES. ASK PIYUSH AGAIN ABOUT HOW DATA ADDRESSES ARE IN MEMORY""" 
						self.memdone = True
				elif self.uidone == True and instruction.maindatabus_busy == True and instruction.databussetter != num and self.memdone == False:
					self.hazards[3] = "Y"  		

			elif self.code[0] == "sw":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False) or (self.uidone == True and instruction.maindatabus_busy == True 
					and instruction.databussetter == num and self.memdone == False)):

					instruction.maindatabus_busy = True
					instruction.databussetter = num
					self.lwcounter = self.lwcounter - 1
					if self.lwcounter == 0:
						self.execstage = True
						self.setdatabusfalse = 1
						"""LOAD STORE WORD ACTUAL LOGIC NEEDED"""
						#lw r1 4(r2)
						#lw r1 r2
						self.memdone = True
				elif self.uidone == True and instruction.maindatabus_busy == True and instruction.databussetter != num and self.memdone == False:
					self.hazards[3] = "Y" 


			elif self.code[0] == "l.d":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False) or (self.uidone == True and instruction.maindatabus_busy == True 
					and instruction.databussetter == num and self.memdone == False)):

					instruction.maindatabus_busy = True
					instruction.databussetter = num
					self.ldcounter = self.ldcounter - 1
					if self.ldcounter == 0:
						self.execstage = True
						self.setdatabusfalse = 1
						self.memdone = True
				elif self.uidone == True and instruction.maindatabus_busy == True and instruction.databussetter != num and self.memdone == False:
					self.hazards[3] = "Y"

			elif self.code[0] == "s.d":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False) or (self.uidone == True and instruction.maindatabus_busy == True 
					and instruction.databussetter == num and self.memdone == False)):

					instruction.maindatabus_busy = True
					instruction.databussetter = num
					self.ldcounter = self.ldcounter - 1
					if self.ldcounter == 0:
						self.execstage = True
						self.setdatabusfalse = 1
						self.memdone = True
				elif self.uidone == True and instruction.maindatabus_busy == True and instruction.databussetter != num and self.memdone == False:
					self.hazards[3] = "Y"





			elif self.code[0] == "dadd" or self.code[0] == "daddi":
				if (self.uidone == False and instruction.mainui_busy == False):
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
				#STRUCTURAL HAZARD THINGY	
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False)):
					instruction.databussetter = num
					instruction.maindatabus_busy = True
					self.execstage = True
					self.setdatabusfalse = 1
					#THE ACTUAL LOGIC FOR ADDITION
					if self.code[0] == "dadd":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) + int(instruction.registers[int(self.code[3][1:])], 2)
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "daddi":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) + int(self.code[3])
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = int(self.code[1][1:])
						instruction.registers[regindex] = answer
					self.memdone = True
				#STRUCTURAL HAZARD THINGY		
				elif self.uidone == True and instruction.maindatabus_busy == True and self.memdone == False:
					self.hazards[3] = "Y"
					

			#DSUB AND DSUBI INSTRUCTIONS
			elif self.code[0] == "dsub" or self.code[0] == "dsubi":
				if (self.uidone == False and instruction.mainui_busy == False):
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
				#STRUCTURAL HAZARD THINGY
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False)):
					instruction.databussetter = num
					instruction.maindatabus_busy = True
					self.execstage = True
					self.setdatabusfalse = 1
					#THE ACTUAL LOGIC FOR ADDITION
					if self.code[0] == "dsub":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) - int(instruction.registers[int(self.code[3][1:])], 2)
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "dsubi":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) - int(self.code[3])
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = int(self.code[1][1:])
						instruction.registers[regindex] = answer
					self.memdone = True
				elif self.uidone == True and instruction.maindatabus_busy == True and self.memdone == False:
					self.hazards[3] = "Y"	
			elif self.code[0] == "and" or self.code[0] == "andi":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True

				#STRUCTURAL HAZARD THINGY
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"		

				elif(self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False):
					instruction.databussetter = num
					instruction.maindatabus_busy = True
					self.execstage = True
					self.setdatabusfalse = 1
					"""ACTUAL BITWISE ANDING"""
					if self.code[0] == "and":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) & int(instruction.registers[int(self.code[3][1:])], 2)
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = 	int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "andi":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) & int(self.code[3][1:])
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = 	int(self.code[1][1:])
						instruction.registers[regindex] = answer
					self.memdone = True
				#STRUCTURAL HAZARD THINGY	
				elif self.uidone == True and instruction.maindatabus_busy == True and self.memdone == False:
					self.hazards[3] = "Y"	



			elif self.code[0] == "or" or self.code[0] == "ori":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
				#STRUCTURAL HAZARD THINGY
				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"
				elif(self.uidone == True and instruction.maindatabus_busy == False and self.memdone == False):
					instruction.databussetter = num
					instruction.maindatabus_busy = True
					self.execstage = True
					self.setdatabusfalse = 1
					"""ACTUAL BITWISE ORING"""
					if self.code[0] == "or":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) | int(instruction.registers[int(self.code[3][1:])], 2)
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = 	int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "ori":
						answer = int(instruction.registers[int(self.code[2][1:])], 2) | int(self.code[3][1:])
						answer = "{0:32b}".format(answer)
						answer = list(answer)
						for i in range(len(answer)):
								if answer[i] == " ":
										answer[i] = "0"
						answer = "".join(answer)
						regindex = 	int(self.code[1][1:])
						instruction.registers[regindex] = answer
					self.memdone = True	
				#STRUCTURAL HAZARD THINGY	
				elif self.uidone == True and instruction.maindatabus_busy == True and self.memdone == False:
					self.hazards[3] = "Y"


			elif self.code[0] == "add.d" or self.code[0] == "sub.d":
				if self.fpa == False:
					if instruction.main_add_pipe == True:
						if instruction.mainadd_busy == False:
							instruction.addsetter = num
							if self.fpalatency == instruction.main_add_latency :
								instruction.mainadd_busy = True
								self.result[1] = counter - 1
								self.setaddfalse = 1
							else:
								pass
							self.fpalatency = self.fpalatency - 1
							if self.fpalatency == 0:
								self.setaddfalse = 1
								self.fpa = True
								self.execstage = True
						elif instruction.mainadd_busy == True:
							self.hazards[3] = "Y"

					elif instruction.main_add_pipe == False:
						if instruction.mainadd_busy == False:
							instruction.addsetter = num
							instruction.mainadd_busy = True
							self.result[1] = counter - 1
							self.fpalatency = self.fpalatency - 1
						elif instruction.mainadd_busy == True and instruction.addsetter == num:
							instruction.addsetter = num
							instruction.mainadd_busy = True
							self.fpalatency = self.fpalatency - 1
							if self.fpalatency == 0:
								self.setaddfalse = 1
								self.fpa = True	
								self.execstage = True							
						elif instruction.mainadd_busy == True and instruction.addsetter != num:
							self.hazards[3] = "Y"	
			elif self.code[0] == "mul.d":
				if self.fpm == False:
					if instruction.mainmul_pipe == True:
						if instruction.mainmul_busy == False:
							instruction.mulsetter = num
							if self.fpmlatency == instruction.mainmul_latency :
								instruction.mainmul_busy = True
								self.result[1] = counter - 1
								self.setmulfalse = 1
							else:
								pass
							self.fpmlatency = self.fpmlatency - 1
							if self.fpmlatency == 0:
								self.setmulfalse = 1
								self.fpm = True
								self.execstage = True
						elif instruction.mainmul_busy == True:
							self.hazards[3] = "Y"
					elif instruction.mainmul_pipe == False:
						if instruction.mainmul_busy == False:
							instruction.mulsetter = num
							instruction.mainmul_busy = True
							self.result[1] = counter - 1
							self.fpmlatency = self.fpmlatency - 1
						elif instruction.mainmul_busy == True and instruction.mulsetter == num:
							instruction.mulsetter = num
							instruction.mainmul_busy = True
							self.fpmlatency = self.fpmlatency - 1
							if self.fpmlatency == 0:
								self.setmulfalse = 1
								self.fpm = True	
								self.execstage = True					
						elif instruction.mainmul_busy == True and instruction.mulsetter != num:
							self.hazards[3] = "Y"

			elif self.code[0] == "div.d":
				if self.fpd == False:
					if instruction.maindiv_pipe == True:
						if instruction.maindiv_busy == False:
							instruction.divsetter = num
							if self.fpdlatency == instruction.maindiv_latency :
								instruction.maindiv_busy = True
								self.result[1] = counter - 1
								self.setdivfalse = 1

							else:
								pass
							self.fpdlatency = self.fpdlatency - 1
							if self.fpdlatency == 0:
								self.setdivfalse = 1
								self.fpd = True
								self.execstage = True
						elif instruction.maindiv_busy == True:
							self.hazards[3] = "Y"		
					elif instruction.maindiv_pipe == False:
						if instruction.mainmul_busy == False:
							instruction.divsetter = num
							instruction.maindiv_busy = True
							self.result[1] = counter - 1
							self.fpdlatency = self.fpdlatency - 1
						elif instruction.maindiv_busy == True and instruction.divsetter == num:
							instruction.divsetter = num
							instruction.maindiv_busy = True
							self.fpdlatency = self.fpdlatency - 1
							if self.fpdlatency == 0:
								self.setdivfalse = 1
								self.fpd = True	
								self.execstage = True
						elif instruction.maindiv_busy == True and instruction.divsetter != num:
							self.hazards[3] == "Y"
		
		elif self.execstage	 == True and self.wbstage == False:
			#CODING IN WRITE BACK PRTIOPRITY
			#BEFORE ACTUALLY PERFORMING A WRITEBACK. GO TO THE END OF THE OBJ_LIST CHECKING IF ANY INSTRUCTION CAN DO A WRITE BACK IN THE SAME CYCLE.
			#IF THERE IS AN INSTRUCTION WHICH CAN DO THAT THEN:
				#IF YOU ARE PIPELINED:
					#IF THAT INSTRUCTION IS NOT PIPELINED:
						#YOU PASS.
					#IF THAT INSTRUCTION IS PIPELINED.
						#IF THAT INSTRUCTION HAS GREATER LATENCY
			#GET WRITE BACK PRIORITY EXPLAINED FROM PIYUSH
			if self.wbstage == False and instruction.mainwb_busy == False:
				self.result[2] = counter - 1
				instruction.mainwb_busy = True
				instruction.wbsetter = num
				self.setwbfalse = 1
				self.wbstage = True
				self.result[3] = counter
			elif instruction.mainwb_busy == True:
				self.hazards[3] = "Y"

		



def main():
	global obj_list
	#Read the instruction file
	code = (open(sys.argv[1], r"U")).readlines()
	parsed_code, labels  = mips_parser.mips_parse(code)
	#<-------TESTING MODULE---------------->
	#for line in parsed_code:
	#	print line
	#print labels
	#<------------------------------------->
	#print "<------------------------------------------------------->"
	#Reading the data file and storing it in a list
	config =filter(lambda k: k != "", [x.strip() for x in (open(sys.argv[4], r"U")).readlines()])
	latencies = []
	pipelined = []	
	#print config
	for i in config:
		temp = i.split(":")
		if "," in temp[1]:
			temp = temp[1].split(",")
			#print temp
		else:
			temp = [temp[1]]
			#print temp
		temp = [x.replace(" ", "").strip() for x in temp]
		if len(temp) == 2:
			latencies.append(temp)
		elif len(temp) == 1:
			pipelined.append(int(temp[0]))
	#print latencies
	#print pipelined
	config = configuration(int(latencies[0][0]), int(latencies[1][0]), int(latencies[2][0]), pipelined[0], pipelined[1], pipelined[2])
	fpa = fpm = fpd = False
	if latencies[0][1].lower() == "yes":
		fpa = True
	if latencies[1][1].lower() == "yes":
		fpm = True
	if latencies[2][1].lower() == "yes":
		fpd = True
	config.set_pipelines(fpa, fpm, fpd)
	#config.printconf()


#<---------------SETTING GLOBALS FOR THE FIRST TIME IN THE INSTRUCTION CLASS--------------------------------------------------------------------------->
	#print "Creating a dummy instruction to set globals"
	dummy = instruction("", None, None, None, None, None)
	instruction.main_add_pipe = config.pipe_fpa
	instruction.mainmul_pipe = config.pipe_fpm
	instruction.maindiv_pipe = config.pipe_fpd
	instruction.main_add_latency = int(config.fpadder)
	instruction.mainmul_latency = int(config.fpmult)
	instruction.maindiv_latency = int(config.fpdiv)
	instruction.mainmemory_latency = int(config.mem)
	instruction.icache_latency = int(config.icac)
	instruction.dcache_latency = int(config.dcac) 
	#print "Compare the two"
	#print instruction.main_add_pipe
	#print instruction.mainmul_pipe
	#print instruction.maindiv_pipe
	#print instruction.main_add_latency
	#print instruction.mainmul_latency
	#print instruction.maindiv_latency
	#print instruction.mainmemory_latency
	#print instruction.icache_latency
	#print instruction.dcache_latency
	#print dummy.main_add_pipe
	#dummy_two = instruction("", None, None, None, None, None)
	#print dummy_two.dcache_latency
	#Find RAW Dependenies in the passed code.
	#The first thing that we need to do is to get a list of destination operands before th einstruction we are looking at. 
	#I write a function which can go thorugh the entire code in a pass and create a dictionary identifying destination operands before your level. 
	destdict =  destination_op_finder.dest_op_finder(parsed_code, labels)
	#<-----------TESTING ROUTINE---------------------->
	#for i in destdict.items():
	#	print i
	#<------------------------------------------------>
	#FINDS RAW DEPENDENCIES
	raw_dict = raw_finder.raw_finder(parsed_code, destdict, labels)
	#THE RAW FINDER RETURNS NO ENTRIES CORRESPONDING TO THOSE WHICH HAVE NO DEPENDENCIES. ADDING NONE FOR SUCH CASE
	for i in range(0, len(parsed_code)):
		if i in raw_dict.keys():
			pass
		else:
			raw_dict[i] = None
	instruction.registers = [x.strip() for x in (open(sys.argv[3], r"U")).readlines()]
	#<------TESTING MODULE----------------->
	#for i in register_data:
	#	print i	
	instruction.memdata = [x.strip() for x in (open(sys.argv[2], r"U")).readlines()]
	#<------TESTING MODULE----------------->
	#for i in memory_data:
	#	print i
	#<------------------------------------->
	#<------------------TESTING ROUTINE----------------------->
	#print "<--------------RAW DICTIONARY---------------->"
	#for i in raw_dict.items():
	#	print i
	#<-----------------TESTING ROUTINE------------------------>I
	#Find WAW HAZARDS and deal with them
	waw_dict = waw_finder.waw_finder(parsed_code, destdict, labels)
	#<-----------------TESTING MODULE------------------------->\
	#Padding the non existing wars with None types
	for i in range(0, len(parsed_code)):
		try:
			temp = waw_dict[i]
		except:
			waw_dict[i] = None
	#print ("<-----------WAW DICTIONARY------------------>")
	#for i in waw_dict.items():
	#	print i
	#<-------------------------------------------------------->
	#FIND WAR HAZARDS BY USING PERIPHERAL INFORMATION.
	war_dict  = war_finder.war_finder(parsed_code, destdict, labels)
	for i in range(0, len(parsed_code)):
		try:
			temp = war_dict[i]
		except:
			war_dict[i]  = None
	#print ("<---------WAR DICTIONARY-------------------->")
	#for i in war_dict.items():
	#	print i

	#<--------------PRODUCE CLEAN CODE WITHOUT LEADING LABELS AND CREATE A LABEL DICTIONARY------------------------------->
	clean_code = []
	label_dict = {}
	for element in range(0, len(parsed_code)):
		if parsed_code[element][0] in labels:
			clean_code.append(parsed_code[element][1:])
			label_dict[parsed_code[element][0]] = element
		else:
			clean_code.append(parsed_code[element])
	#for line in clean_code:
	#	print line
	#print label_dict.items()
	#<--------------INITIALIZE CODE OBJECTS IN A LIST CALLED OBJ_LIST-------------->
	instruction.label_dictionary = label_dict
	for i in range(0, len(clean_code)):
		obj_list.append(instruction(clean_code[i], raw_dict[i], war_dict[i], waw_dict[i], destdict[i], i ))

	for i in range(0, len(clean_code)):
		instruction.ref_objlist.append(instruction(clean_code[i], raw_dict[i], war_dict[i], waw_dict[i], destdict[i], i ))
	#print obj_list
	#print "----------------------"
	#print instruction.ref_objlist
	print raw_dict[10]
	counter = 1
	while(obj_list[-1].result[0] == None):
		for num in range(0, len(obj_list)):
			if obj_list[num].hideme == 0:
				obj_list[num].action(num, counter)
		#IF STAGE
		if obj_list[instruction.ifsetter].setiffalse == 1:
			instruction.mainif_busy = False
		#ID STAGE
		if obj_list[instruction.idsetter].setidfalse == 1:
			instruction.mainid_busy = False
		#UI
		if obj_list[instruction.uisetter].setuifalse == 1:
			instruction.mainui_busy = False
		#DATABUS
		if obj_list[instruction.databussetter].setdatabusfalse == 1:
			instruction.maindatabus_busy = False
		#ADDER
		if obj_list[instruction.addsetter].setaddfalse == 1:
			instruction.mainadd_busy = False
		#MULTIPLIER
		if obj_list[instruction.mulsetter].setmulfalse == 1:
			instruction.mainmul_busy = False
		#DIVIDER
		if obj_list[instruction.divsetter].setdivfalse == 1:
			instruction.maindiv_busy = False
		#WRITEBACK STAGE
		if obj_list[instruction.wbsetter].setwbfalse == 1:
			instruction.mainwb_busy = False
		counter = counter + 1
		#for i in obj_list:
		#	print i.result
		#	print "------------"
		#print "---------------------------------------------------"	
		#if counter == 50:
			#for number, i in enumerate(obj_list):
			#	print "I am" + str(number) + "and my hidden bit is " + str(i.hideme)
		#	break
	#print obj_list[0].result[0]
	#print obj_list[0].ifstage
	#print obj_list[0].idstage
	#print obj_list[0].execstage
	#shit = instruction.registers[0]
	#print instruction.registers.index(shit)
	#print instruction.memdata
	for i in obj_list:
		print i.result,
		print i.hazards
		print "------------"
if __name__ == "__main__":
	main()

