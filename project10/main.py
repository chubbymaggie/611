#!/usr/bin/python
import sys
import mips_parser
import destination_op_finder
import raw_finder
import waw_finder
import war_finder
import re

#LOGICS FOR LW AND SW ARE YET TO BE IMPLEMENTED. 
#LOGICS FOR SOME ARITHMENATIC OPERATIONS MIGHT NOT BE IMPLEMENTED. -- Done
#WRITEBACK PRIORITY HAS NOT BEEN IMPLEMENTED. 
#SELF.LINE_OF_CODE CAN BE USED AS ADDRESS NUMBER. -- Done 
#WHEREVER DATABUS IS BEING USED. I HAVE TO ADD A CASE IN THOSE CASES HWERE MAINDATABUS_BUSY IS FAlse, to 
#make sure icache bus request is not true -- Probably done. Need to make sure.
#FOR ID STAGE WHERE BRANCHES ARE TAKEND AND I JUST GO AHEAD AND WRITE THE NEXT STAGE COUNTER. SEE IF THE NEXT INSTRUCTION
#IS ACTUALLY IN ICACHE, IF SO WRITE, IF NOT MOVE ON. -- Not done
#DATA HAS TO BE CONVERTED INTO A DICTIONARY FILE THAT HAS ADDRESSING FROM 256 Onwards. -- Done
#instruction i-cachelatency and dcachelatency need to be set from outside.
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
	dcache = []
	dcache_busy = False
	dcachesetter = 0
	dcache_setzero_block_zero_dirty = 0
	dcache_setone_block_zero_dirty = 0
	dcache_setzero_block_one_dirty = 0
	dcache_setone_block_one_dirty = 0
	lru_block_zero = None
	lru_block_one = None
	zero_block = []
	one_block = []
	#THE INSTRUCTION CACHE
	instruction_cache = []	
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
	icache_latency = 1 #THESE ARE JUST PLACE HOLDER VALUES, THEY GET SET WHEN AN INSTANCE OF CLASS IS CREATED
	dcache_latency = 1 #THESE ARE JUST PLACE HOLDER VALUES, THEY GET SET WHEN AN INSTANCE OF CLASS IS CREATED
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
	memdata = {}
	mem = False
	memsetter = 0
	memblocks = []
	instructionbusrequest = False #Indicatest that an IF Stage has made a bus request.
	instructioncachemaincount = 0
	instructioncachehitcount = 0
	datacachemaincount = 0
	datacachehitcount = 0

	def __init__(self, code, raw_list, war_list, waw_list, dest, line_of_code):
		self.ldstageone = False
		self.ldstagetwo = False
		self.ldstagethree = False
		self.ldstagefour = False
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
		self.ifcache_miss = False
		self.instructionloadcounter = 2 * (instruction.icache_latency + instruction.mainmemory_latency)
		self.setmemfalse = 0
		self.icache_hit = 0
		self.icachelatency = instruction.icache_latency
		self.dcacheldhitstracker = [0, 0]
		self.lddirtytracker = [0, 0]
		self.ldonecachelatency = 0
		self.ldonememlatency = 0
		self.ldtwocachelatency = 0
		self.ldtwomemlatency = 0
		self.dcachelwhittracker = 0
		self.dcacheswhittracker = 0
		self.lwdirtytracker = 0
		self.lwcachelatency = 0
		self.lwmemlatency = 0
		self.lwstageone = False
		self.lwstagetwo = False
		self.sworiginaldirtytracker = 0
		self.swcachelatency = 0
		self.swmemlatency = 0
		self.swstageone = False
		self.swstagetwo = False

	def action(self, num, counter):
		global obj_list
		#"""WRITING THE IF STAGE FUNCTIONALITY HERE"""
		if(self.ifstage == False):
			#print "Entrered IF"
			#IF THE MAINIF IS NOT BUSY AND THE PREVIOUS ID STAGE IS COMPLETE AND I AM NOT 
			if((instruction.mainif_busy == False) and ((num == 0) or (obj_list[num - 1].idstage == True)) or (instruction.mainif_busy == True and instruction.ifsetter == num and self.icache_hit == 1)):
				instruction.mainif_busy = True
				instruction.ifsetter = num
				instruction.instructioncachemaincount += 1
				#IF THE INSTRUCTION IS IN CACHE:
				if self.line_of_code in [x[0] for x in instruction.instruction_cache]:
					self.icache_hit = 1
					self.icachelatency = self.icachelatency - 1
					if self.icachelatency == 0:
						instruction.instructioncachehitcount += 1
						self.icache_hit = 1
						self.setiffalse = 1
						self.ifstage = True
				elif self.line_of_code not in [x[0] for x in instruction.instruction_cache]:
					instruction.instructionbusrequest = True
					self.ifcache_miss = True
					#ACTUALLY FILL THE CACHE WITH ALL THE FOUR WORDS AND DO TIME PASS FOR THE NEXT AS MANY CYCLES
					if self.line_of_code in [0, 16, 32, 48]:
						instruction.instruction_cache[0][0] = self.line_of_code
						instruction.instruction_cache[1][0] = self.line_of_code + 1
						instruction.instruction_cache[2][0] = self.line_of_code + 2
						instruction.instruction_cache[3][0] = self.line_of_code + 3
					elif self.line_of_code in [1, 17, 33, 49]:
						instruction.instruction_cache[0][0] = self.line_of_code - 1
						instruction.instruction_cache[1][0] = self.line_of_code 
						instruction.instruction_cache[2][0] = self.line_of_code + 1
						instruction.instruction_cache[3][0] = self.line_of_code + 2
					elif self.line_of_code in [2, 18, 34, 50]:
						instruction.instruction_cache[0][0] = self.line_of_code - 2
						instruction.instruction_cache[1][0] = self.line_of_code - 1
						instruction.instruction_cache[2][0] = self.line_of_code 
						instruction.instruction_cache[3][0] = self.line_of_code + 1
					elif self.line_of_code in [3, 19, 35, 51]:
						instruction.instruction_cache[0][0] = self.line_of_code - 3
						instruction.instruction_cache[1][0] = self.line_of_code - 2 
						instruction.instruction_cache[2][0] = self.line_of_code - 1
						instruction.instruction_cache[3][0] = self.line_of_code
					#---------------BLOCK 2 REPLACEMENTS IN I-CACHE--------------#	
					elif self.line_of_code in [4, 20, 36, 52]:
						instruction.instruction_cache[4][0] = self.line_of_code 
						instruction.instruction_cache[5][0] = self.line_of_code + 1 
						instruction.instruction_cache[6][0] = self.line_of_code + 2
						instruction.instruction_cache[7][0] = self.line_of_code	+ 3 
					elif self.line_of_code in [5, 21, 37, 53]:
						instruction.instruction_cache[4][0] = self.line_of_code - 1
						instruction.instruction_cache[5][0] = self.line_of_code 
						instruction.instruction_cache[6][0] = self.line_of_code + 1
						instruction.instruction_cache[7][0] = self.line_of_code + 2
					elif self.line_of_code in [6, 22, 38, 54]:
						instruction.instruction_cache[4][0] = self.line_of_code - 2
						instruction.instruction_cache[5][0] = self.line_of_code - 1
						instruction.instruction_cache[6][0] = self.line_of_code 
						instruction.instruction_cache[7][0] = self.line_of_code + 1
					elif self.line_of_code in [7, 23, 39, 55]:
						instruction.instruction_cache[4][0] = self.line_of_code - 3
						instruction.instruction_cache[5][0] = self.line_of_code - 2 
						instruction.instruction_cache[6][0] = self.line_of_code - 1
						instruction.instruction_cache[7][0] = self.line_of_code	
					#-------------------BLOCK 3 REPLACEMENTS IN I-CAHCE------------#
					elif self.line_of_code in [8, 24, 40, 56]:
						instruction.instruction_cache[8][0] = self.line_of_code 
						instruction.instruction_cache[9][0] = self.line_of_code + 1 
						instruction.instruction_cache[10][0] = self.line_of_code + 2
						instruction.instruction_cache[11][0] = self.line_of_code	+ 3 
					elif self.line_of_code in [9, 25, 41, 57]:
						instruction.instruction_cache[8][0] = self.line_of_code - 1
						instruction.instruction_cache[9][0] = self.line_of_code 
						instruction.instruction_cache[10][0] = self.line_of_code + 1
						instruction.instruction_cache[11][0] = self.line_of_code + 2
					elif self.line_of_code in [10, 26, 42, 58]:
						instruction.instruction_cache[8][0] = self.line_of_code - 2
						instruction.instruction_cache[9][0] = self.line_of_code - 1
						instruction.instruction_cache[10][0] = self.line_of_code 
						instruction.instruction_cache[11][0] = self.line_of_code + 1
					elif self.line_of_code in [11, 27, 43, 59]:
						instruction.instruction_cache[8][0] = self.line_of_code - 3
						instruction.instruction_cache[9][0] = self.line_of_code - 2 
						instruction.instruction_cache[10][0] = self.line_of_code - 1
						instruction.instruction_cache[11][0] = self.line_of_code
					#BLOCK 4 FOR I - CACHE REPLACEMENT	
					elif self.line_of_code in [12, 28, 44, 60]:
						instruction.instruction_cache[8][0] = self.line_of_code 
						instruction.instruction_cache[9][0] = self.line_of_code + 1 
						instruction.instruction_cache[10][0] = self.line_of_code + 2
						instruction.instruction_cache[11][0] = self.line_of_code	+ 3 
					elif self.line_of_code in [13, 29, 45, 61]:
						instruction.instruction_cache[8][0] = self.line_of_code - 1
						instruction.instruction_cache[9][0] = self.line_of_code 
						instruction.instruction_cache[10][0] = self.line_of_code + 1
						instruction.instruction_cache[11][0] = self.line_of_code + 2
					elif self.line_of_code in [14, 30, 46, 62]:
						instruction.instruction_cache[8][0] = self.line_of_code - 2
						instruction.instruction_cache[9][0] = self.line_of_code - 1
						instruction.instruction_cache[10][0] = self.line_of_code 
						instruction.instruction_cache[11][0] = self.line_of_code + 1
					elif self.line_of_code in [15, 31, 47, 63]:
						instruction.instruction_cache[8][0] = self.line_of_code - 3
						instruction.instruction_cache[9][0] = self.line_of_code - 2 
						instruction.instruction_cache[10][0] = self.line_of_code - 1
						instruction.instruction_cache[11][0] = self.line_of_code
					self.instructionloadcounter = self.instructionloadcounter - 1	
			elif((instruction.mainif_busy == True) and (instruction.ifsetter == num) and self.ifcache_miss == True and instruction.instructionbusrequest == True):
				if (instruction.maindatabus_busy == False) or (instruction.maindatabus_busy == True and instruction.databussetter == num):
					instruction.maindatabus_busy = True
					instruction.databussetter = num
					self.instructionloadcounter = self.instructionloadcounter - 1
					#print self.instructionloadcounter
					if self.instructionloadcounter == 0:
						self.setdatabusfalse = 1
						self.setiffalse = 1
						self.ifstage = True
						instruction.instructionbusrequest = False
						#print "IF Complete"


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
				#print "Entered ID"
				for elements in self.raw:
					#print "Stuck in raw"
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
						#HAVE TO DEFINE THE SHAMNUM VARIABLE. ABSOLUTELY HAVE TO.
						shamnum = self.line_of_code  + 1
						if shamnum in [x[0] for x in instruction.instruction_cache]:
							instruction.instructioncachemaincount += 1
							instruction.instructioncachehitcount += 1
							obj_list[num + 1].result[0] = counter
						elif shamnum not in [x[0] for x in instruction.instruction_cache]:
							instruction.instructioncachemaincount += 1
							obj_list[num + 1].result[0] = counter + 2 * (instruction.icache_latency + instruction.mainmemory_latency) - 1		
						instruction.ifsetter = num + 1
						obj_list[num + 1].setiffalse = 1

					elif self.code[0] == "bne":
						if instruction.registers[int(self.code[1][1:])] != instruction.registers[int(self.code[2][1:])]:
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
								instruction.instructioncachemaincount += 1
								if self.line_of_code + 1 in [x[0] for x in instruction.instruction_cache]:
									obj_list[num + 1].result[0] = counter
									instruction.instructioncachehitcount += 1
								instruction.ifsetter = num + 1
								obj_list[num + 1].setiffalse = 1	
								#THIS LINE IS EXTREMELY IMPORTANT.
								obj_list.extend(instruction.ref_objlist[jumper:])
						else:
							self.result[1] = counter
							self.execstage = True
							self.wbstage = True				

					elif self.code[0] == "beq":
						if instruction.registers[int(self.code[1][1:])] == instruction.registers[int(self.code[2][1:])]:
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
								instruction.instructioncachemaincount += 1
								if self.line_of_code + 1 in [x[0] for x in instruction.instruction_cache]:
									obj_list[num + 1].result[0] = counter
									instruction.instructioncachehitcount += 1
								instruction.ifsetter = num + 1
								obj_list[num + 1].setiffalse = 1	
								#THIS LINE IS EXTREMELY IMPORTANT.
								obj_list.extend(instruction.ref_objlist[jumper:])
						else:
							self.result[1] = counter
							self.execstage = True
							self.wbstage = True
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
					if "(" in self.code[2]:
						#lw r1 4(r10)
						#lw r2 4(r3)
						address = int(self.code[2].split("(")[0]) + instruction.registers[int(re.search("\((\w\d+)\)", self.code[2]).group(1)[1:])]
						if address in instruction.zero_block:
							bit = 0
						elif address in instruction.one_block:
							bit = 1	
					elif "(" not in self.code[2]:
						#lw r1 r21
						#lw r1 r21
						address = int(instruction.registers[int(self.code[2][1:])])
						if address in instruction.zero_block:
							bit = 0
						elif address in instruction.one_block:
							bit = 1

					if bit == 0:
						instruction.datacachemaincount += 1
						addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]
						addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]
						if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
							instruction.datacachehitcount += 1
							#print self.dcacheldhitstracker
							self.dcachelwhittracker = 1 #SIGNIFIES A CACHE HIT
							if address in addresses_in_first_cache:
								index = addresses_in_first_cache.index(address)
								content = instruction.dcache[0][0][index][1]
								instruction.registers[int(self.code[1][1:])] = content
								#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
								instruction.lru_block_zero = 1
							elif address in addresses_in_second_cache:
								index = addresses_in_second_cache.index(address)
								content = instruction.dcache[1][0][index][1]
								instruction.registers[int(self.code[1][1:])] = content
								instruction.lru_block_zero = 0 	
						elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
							self.dcachelwhittracker = 0
							if addresses_in_first_cache == [None, None, None, None]:
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0, 4):
									instruction.dcache[0][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]	
								index = addresses_in_first_cache.index(address)
								content = instruction.dcache[0][0][index][1]
								instruction.registers[int(self.code[1][1:])] = content		
								instruction.lru_block_zero = 1	
							elif addresses_in_second_cache == [None, None, None, None]:	
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0,4):
									instruction.dcache[1][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]	
								index = addresses_in_second_cache.index(address)
								content = instruction.dcache[1][0][index][1]
								instruction.registers[int(self.code[1][1:])] = content
								instruction.lru_block_zero = 0				
							elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:
								if lru_block_zero == 0:
									#REPLACE BLOCK 0 OF SET ZERO. 
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instruction.dcache[0][0]
									for i in range(0, 4):
										instruction.dcache[0][0][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
										#Writing back regardless	
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setzero_block_zero_dirty == 1:
										self.lwdirtytracker = 1
										#COZ THIS NOW HAVE VALUES FRESH FROM MEMORY
										instruction.dcache_setzero_block_zero_dirty = 0
									addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]	
									index = addresses_in_first_cache.index(address)
									content = instruction.dcache[0][0][index][1]
									instruction.registers[int(self.code[1][1:])] = content
									#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
									instruction.lru_block_zero = 1	

								elif lru_block_zero == 1:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instruction.dcache[1][0]
									for i in range(0, 4):
										instruction.dcache[1][0][i]	= [temp_holder[i], instruction.memdata[temp_holder[i]]]
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setone_block_zero_dirty == 1:
										self.lwdirtytracker = 1
										instruction.dcache_setone_block_zero_dirty = 0
									addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]
									index = addresses_in_second_cache.index(address)
									content = instruction.dcache[1][0][index][1]
									instruction.registers[int(self.code[1][1:])] = content
									instruction.lru_block_zero = 0	
					

					elif bit == 1:	
						instruction.datacachemaincount += 1
						addresses_in_first_cache = [x[0] for x in instruction.dcache[0][1]]
						addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]
						if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
							instruction.datacachehitcount += 1
							self.dcachelwhittracker = 1 #SIGNIFIES A CACHE HIT
							if address in addresses_in_first_cache:
								index = addresses_in_first_cache.index(address)
								content = instruction.dcache[0][1][index][1]
								instruction.registers[int(self.code[1][1:])] = content
								#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
								instruction.lru_block_one = 1
							elif address in addresses_in_second_cache:
								index = addresses_in_second_cache.index(address)
								content = instruction.dcache[1][1][index][1]	
								instruction.registers[int(self.code[1][1:])] = content
								instruction.lru_block_one = 0
						elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
							self.dcachelwhittracker = 0
							if addresses_in_first_cache == [None, None, None, None]:		
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0, 4):
									instruction.dcache[0][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_first_cache = [x[0] for x in instructions.dcache[0][1]]	
								index = addresses_in_first_cache.index(address)
								content = instruction.dcache[0][1][index][1]
								instruction.registers[int(self.code[1][1:])] = content		
								instruction.lru_block_one = 1
							elif addresses_in_second_cache == [None, None , None, None]:	
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0,4):
									instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]	
								index = addresses_in_second_cache.index(address)
								content = instruction.dcache[1][1][index][1]	
								instruction.registers[int(self.code[1][1:])] = content			
								instruction.lru_block_one = 0
							elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:	
								if lru_block_one == 0:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instruction.dcache[0][1]
									for i in range(0, 4):
										instruction.dcache[0][1][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
									#Writing back regardless	
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setzero_block_one_dirty == 1:
										self.lwdirtytracker = 1
										instruction.dcache_setzero_block_one_dirty = 0
									addresses_in_first_cache = [x[0] for x in instruction.dcache[0][1]]	
									index = addresses_in_first_cache.index(address)
									content = instruction.dcache[0][1][index][1]
									instruction.registers[int(self.code[1][1:])] = content			
									instruction.lru_block_one = 1
								elif lru_block_one == 1:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instrucion.dcache[1][1]
									for i in range(0, 4):
										instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]			
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setone_block_one_dirty == 1:
										self.lwdirtytracker = 1
										instruction.dcache_setone_block_one_dirty = 0
									addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]	
									index = addresses_in_second_cache.index(address)
									content = instruction.dcache[1][1][index][1]	
									instruction.registers[int(self.code[1][1:])] = content			
									instruction.lru_block_one = 0					

					if self.dcachelwhittracker == 1:
						self.lwcachelatency = instruction.dcache_latency
						self.lwmemlatency = 0
						self.lwstagetwo = True
					elif self.dcachelwhittracker == 0:
						self.lwcachelatency = 0
						self.lwstageone = True
						if self.lwdirtytracker == 0:
							self.lwmemlatency = 2 * (instruction.dcache_latency + instruction.mainmemory_latency)
						elif self.lwdirtytracker == 1:
							self.lwmemlatency = 4 * (instruction.dcache_latency + instruction.mainmemory_latency)						







				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.mem == False and self.memdone == False) or (self.uidone == True and instruction.mem == True 
					and instruction.memsetter == num and self.memdone == False)):
					#print "Entered exec"
					instruction.memsetter = num
					instruction.mem = True
					#print self.lwstageone
					if self.lwstageone == False:
						self.lwcachelatency = self.lwcachelatency - 1
						if self.lwcachelatency == 0:
							self.lwstageone = True
							if self.lwstagetwo == True:
								self.execstage = True
								#print "Exec turned to True"
								self.setdatabusfalse = 1
								#lw r1 4(r2)
								#lw r1 r2
								self.memdone = True
								self.setmemfalse = 1	
					elif self.lwstagetwo == False:
						#print "Entered Stage two"
						if (instruction.maindatabus_busy == False  and instruction.instructionbusrequest == False) or (instruction.maindatabus_busy == True and instruction.databussetter == num ):
							instruction.maindatabus_busy = True
							#print "Bus taken"
							instruction.databussetter = num
							#print self.lwmemlatency
							self.lwmemlatency = self.lwmemlatency - 1
							#print self.lwmemlatency
							if self.lwmemlatency == 0:
								#print "Exec turned to True"
								self.execstage = True
								self.setdatabusfalse = 1
								#lw r1 4(r2)
								#lw r1 r2
								self.memdone = True
								self.setmemfalse = 1
					#print "self.uidone " + str(self.uidone)
					#print "instruction.mem" + str(instruction.mem)
					#print "instruction.memsetter" + str(instruction.memsetter)	
					#print "self.memdone" + str(self.memdone)
					#print "self.exex" + str(self.execstage)		
				elif self.uidone == True and instruction.mem == True and instruction.memsetter != num and self.memdone == False:
					self.hazards[3] = "Y"  		



			if self.code[0] == "sw":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
					if "(" in self.code[2]:
						#lw r1 4(r10)
						#lw r2 4(r3)
						address = int(self.code[2].split("(")[0]) + instruction.registers[int(re.search("\((\w\d+)\)", self.code[2]).group(1)[1:])]
						if address in instruction.zero_block:
							bit = 0
						elif address in instruction.one_block:
							bit = 1	
					elif "(" not in self.code[2]:
						#lw r1 r21
						#lw r1 r21
						address = int(instruction.registers[int(self.code[2][1:])])
						if address in instruction.zero_block:
							bit = 0
						elif address in instruction.one_block:
							bit = 1

					if bit == 0:
						instruction.datacachemaincount += 1
						addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]
						addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]
						if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
							instruction.datacachehitcount += 1
							#print self.dcacheldhitstracker
							self.dcachelwhittracker = 1 #SIGNIFIES A CACHE HIT
							if address in addresses_in_first_cache:
								index = addresses_in_first_cache.index(address)
								content = instruction.registers[int(self.code[1][1:])]
								instruction.registers[int(self.code[1][1:])] = content
								#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
								instruction.dcache_setzero_block_zero_dirty = 1
								instruction.lru_block_zero = 1
							elif address in addresses_in_second_cache:
								index = addresses_in_second_cache.index(address)
								content = instruction.registers[int(self.code[1][1:])]
								instruction.dcache[1][0][index][1] = content
								instruction.dcache_setone_block_zero_dirty = 1
								instruction.lru_block_zero = 0 	
						elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
							self.dcachelwhittracker = 0
							if addresses_in_first_cache == [None, None, None, None]:
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0, 4):
									instruction.dcache[0][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]	
								index = addresses_in_first_cache.index(address)
								content = instruction.registers[int(self.code[1][1:])]
								instruction.dcache[0][0][index][1] = content
								instruction.dcache_setzero_block_zero_dirty = 1		
								instruction.lru_block_zero = 1	
							elif addresses_in_second_cache == [None, None, None, None]:	
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0,4):
									instruction.dcache[1][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]	
								index = addresses_in_second_cache.index(address)
								content =  instruction.registers[int(self.code[1][1:])]
								instruction.dcache[1][0][index][1] = content
								instruction.dcache_setone_block_zero_dirty = 1
								instruction.lru_block_zero = 0				
							elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:
								if lru_block_zero == 0:
									#REPLACE BLOCK 0 OF SET ZERO. 
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instruction.dcache[0][0]
									for i in range(0, 4):
										instruction.dcache[0][0][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
										#Writing back regardless	
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setzero_block_zero_dirty == 1:
										self.lwdirtytracker = 1
										#COZ THIS NOW HAVE VALUES FRESH FROM MEMORY
										instruction.dcache_setzero_block_zero_dirty = 0
									addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]	
									index = addresses_in_first_cache.index(address)
									content =  instruction.registers[int(self.code[1][1:])]
									instruction.dcache[0][0][index][1] = content
									#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
									instruction.lru_block_zero = 1	
									instruction.dcache_setzero_block_zero_dirty = 1

								elif lru_block_zero == 1:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instruction.dcache[1][0]
									for i in range(0, 4):
										instruction.dcache[1][0][i]	= [temp_holder[i], instruction.memdata[temp_holder[i]]]
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setone_block_zero_dirty == 1:
										self.lwdirtytracker = 1
										instruction.dcache_setone_block_zero_dirty = 0
									addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]
									index = addresses_in_second_cache.index(address)
									content =  instruction.registers[int(self.code[1][1:])]
									instruction.dcache[1][0][index][1] = content
									instruction.dcache_setone_block_zero_dirty = 1
									instruction.lru_block_zero = 0	
					

					elif bit == 1:
						instruction.datacachemaincount += 1	
						addresses_in_first_cache = [x[0] for x in instruction.dcache[0][1]]
						addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]
						if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
							instruction.datacachehitcount += 1
							self.dcachelwhittracker = 1 #SIGNIFIES A CACHE HIT
							if address in addresses_in_first_cache:
								index = addresses_in_first_cache.index(address)
								content =  instruction.registers[int(self.code[1][1:])]
								instruction.dcache[0][1][index][1] = content
								#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
								instruction.dcache_setzero_block_one_dirty = 1
								instruction.lru_block_one = 1
							elif address in addresses_in_second_cache:
								index = addresses_in_second_cache.index(address)
								content = instruction.registers[int(self.code[1][1:])]	
								instruction.dcache[1][1][index][1] = content
								instruction.dcache_setone_block_one_dirty = 1
								instruction.lru_block_one = 0
						elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
							self.dcachelwhittracker = 0
							if addresses_in_first_cache == [None, None, None, None]:		
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0, 4):
									instruction.dcache[0][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_first_cache = [x[0] for x in instructions.dcache[0][1]]	
								index = addresses_in_first_cache.index(address)
								content = instruction.registers[int(self.code[1][1:])]
								instruction.dcache[0][1][index][1] = content
								instruction.dcache_setzero_block_one_dirty = 1		
								instruction.lru_block_one = 1
							elif addresses_in_second_cache == [None, None , None, None]:	
								for i in instruction.memblocks:
									if address in i:
										temp_holder = i
										break
								for i in range(0,4):
									instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
								addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]	
								index = addresses_in_second_cache.index(address)
								content =  instruction.registers[int(self.code[1][1:])]	
								instruction.dcache[1][1][index][1] = content
								instruction.dcache_setone_block_one_dirty = 1			
								instruction.lru_block_one = 0
							elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:	
								if lru_block_one == 0:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instruction.dcache[0][1]
									for i in range(0, 4):
										instruction.dcache[0][1][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
									#Writing back regardless	
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setzero_block_one_dirty == 1:
										self.lwdirtytracker = 1
										instruction.dcache_setzero_block_one_dirty = 0
									addresses_in_first_cache = [x[0] for x in instruction.dcache[0][1]]	
									index = addresses_in_first_cache.index(address)
									content = instruction.registers[int(self.code[1][1:])]
									instruction.dcache[0][1][index][1] = content	
									instruction.dcache_setzero_block_one_dirty = 1		
									instruction.lru_block_one = 1
								elif lru_block_one == 1:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									temp_holder_two = instrucion.dcache[1][1]
									for i in range(0, 4):
										instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]			
									for i in temp_holder_two:
										instruction.memdata[i[0]] = i[1]
									if instruction.dcache_setone_block_one_dirty == 1:
										self.lwdirtytracker = 1
										instruction.dcache_setone_block_one_dirty = 0
									addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]	
									index = addresses_in_second_cache.index(address)
									content = instruction.registers[int(self.code[1][1:])]	
									instruction.dcache[1][1][index][1] = content
									instruction.dcache_setone_block_one_dirty = 1			
									instruction.lru_block_one = 0					

					if self.dcachelwhittracker == 1:
						self.lwcachelatency = instruction.dcache_latency
						self.lwmemlatency = 0
						self.lwstagetwo = True
					elif self.dcachelwhittracker == 0:
						self.lwcachelatency = 0
						self.lwstageone = True
						if self.lwdirtytracker == 0:
							self.lwmemlatency = 2 * (instruction.dcache_latency + instruction.mainmemory_latency)
						elif self.lwdirtytracker == 1:
							self.lwmemlatency = 4 * (instruction.dcache_latency + instruction.mainmemory_latency)						







				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.mem == False and self.memdone == False) or (self.uidone == True and instruction.mem == True 
					and instruction.memsetter == num and self.memdone == False)):
					#print "Entered exec"
					instruction.memsetter = num
					instruction.mem = True
					#print self.lwstageone
					if self.lwstageone == False:
						self.lwcachelatency = self.lwcachelatency - 1
						if self.lwcachelatency == 0:
							self.lwstageone = True
							if self.lwstagetwo == True:
								self.execstage = True
								#print "Exec turned to True"
								self.setdatabusfalse = 1
								#lw r1 4(r2)
								#lw r1 r2
								self.memdone = True
								self.setmemfalse = 1	
					elif self.lwstagetwo == False:
						#print "Entered Stage two"
						if (instruction.maindatabus_busy == False  and instruction.instructionbusrequest == False) or (instruction.maindatabus_busy == True and instruction.databussetter == num ):
							instruction.maindatabus_busy = True
							#print "Bus taken"
							instruction.databussetter = num
							#print self.lwmemlatency
							self.lwmemlatency = self.lwmemlatency - 1
							#print self.lwmemlatency
							if self.lwmemlatency == 0:
								#print "Exec turned to True"
								self.execstage = True
								self.setdatabusfalse = 1
								#lw r1 4(r2)
								#lw r1 r2
								self.memdone = True
								self.setmemfalse = 1
					#print "self.uidone " + str(self.uidone)
					#print "instruction.mem" + str(instruction.mem)
					#print "instruction.memsetter" + str(instruction.memsetter)	
					#print "self.memdone" + str(self.memdone)
					#print "self.exex" + str(self.execstage)		
				elif self.uidone == True and instruction.mem == True and instruction.memsetter != num and self.memdone == False:
					self.hazards[3] = "Y"		









			elif self.code[0] == "l.d":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
					#FINDING THE ADDRESSES IN LOAD DOUBLE WORD. BOTH ADDRESSSES ARE FOUND AND STORED IN AN ARRAY WITH CORRESPONDING BITS:
					if "(" in self.code[2]:
						block_bits = []
						addresses_array = []
						#lw r1 4(r10)
						#lw r2 4(r3)
						address_one = int(self.code[2].split("(")[0]) + instruction.registers[int(re.search("\((\w\d+)\)", self.code[2]).group(1)[1:])]
						if address_one in instruction.zero_block:
							block_bits.append(0)
						elif address_one in instruction.one_block:
							block_bits.append(1)	
						address_two = address_one + 4
						if address_two in instruction.zero_block:
							block_bits.append(0)
						elif address_two in instruction.one_block:
							block_bits.append(1)
						addresses_array.append(address_one)
						addresses_array.append(address_two)
						#instruction.registers[self.code[]]
					elif "(" not in self.code[2]:
						block_bits = []
						addresses_array = []
						#lw r1 r21
						#lw r1 r21
						address_one = int(instruction.registers[int(self.code[2][1:])])
						if address_one in instruction.zero_block:
							block_bits.append(0)
						elif address_one in instruction.one_block:
							block_bits.append(1)
						address_two = address_one + 4
						if address_two in instruction.zero_block:
							block_bits.append(0)
						elif address_two in instruction.one_block:
							block_bits.append(1)
						addresses_array.append(address_one)
						addresses_array.append(address_two)

					#print "**********************PRINTING BLOCK BITS*********************************"
					#print block_bits
					#print "**************************************************************************"
					#print "*************************PRINTING ADDRESSES*******************************"
					#print addresses_array
					#print "**************************************************************************"		
					for goodstuff in range(len(addresses_array)):
						address = addresses_array[goodstuff]
						bit = block_bits[goodstuff]
						if bit == 0:
							instruction.datacachemaincount += 1
							addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]
							addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]
							if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
								instruction.datacachehitcount += 1
								#print self.dcacheldhitstracker
								self.dcacheldhitstracker[goodstuff] = 1 #SIGNIFIES A CACHE HIT
								if address in addresses_in_first_cache:
									index = addresses_in_first_cache.index(address)
									#THE BELOW LINE SHOULD NEVER BE UNCOMMENTED
									#content = instruction.dcache[0][0][index][1]
									#instruction.registers[int(self.code[1][1:])] = content
									#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
									instruction.lru_block_zero = 1
								elif address in addresses_in_second_cache:
									index = addresses_in_second_cache.index(address)
									#content = instruction.dcache[1][0][index][1]
									#THE BELOW LINW SHOULD NEVER BE UNCOMMENTED SINCE THIS IS L.D
									#instruction.registers[int(self.code[1][1:])] = content
									instruction.lru_block_zero = 0 	
							elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
								self.dcacheldhitstracker[goodstuff] = 0
								if addresses_in_first_cache == [None, None, None, None]:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0, 4):
										instruction.dcache[0][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]	
									instruction.lru_block_zero = 1	
								elif addresses_in_second_cache == [None, None, None, None]:	
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0,4):
										instruction.dcache[1][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]		
									instruction.lru_block_zero = 0	

								elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:
									if lru_block_zero == 0:
										#REPLACE BLOCK 0 OF SET ZERO. 
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instruction.dcache[0][0]
										for i in range(0, 4):
											instruction.dcache[0][0][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
										#Writing back regardless	
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setzero_block_zero_dirty == 1:
											self.lddirtytracker[goodstuff]= 1
											instruction.dcache_setzero_block_zero_dirty = 0
										instruction.lru_block_zero = 1
									elif lru_block_zero == 1:
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instruction.dcache[1][0]
										for i in range(0, 4):
											instruction.dcache[1][0][i]	= [temp_holder[i], instruction.memdata[temp_holder[i]]]
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setone_block_zero_dirty == 1:
											self.lddirtytracker[goodstuff] = 1
											instruction.dcache_setone_block_zero_dirty = 0
										instruction.lru_block_zero = 0							




						elif bit == 1:
							instruction.datacachemaincount += 1	
							addresses_in_first_cache = [x[0] for x in instruction.dcache[0][1]]
							addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]
							if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
								instruction.datacachehitcount += 1
								self.dcacheldhitstracker[goodstuff] = 1 #SIGNIFIES A CACHE HIT
								if address in addresses_in_first_cache:
									index = addresses_in_first_cache.index(address)
									#content = instruction.dcache[0][1][index][1]
									#instruction.registers[int(self.code[1][1:])] = content
									#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
									instruction.lru_block_one = 1
								elif address in addresses_in_second_cache:
									index = addresses_in_second_cache.index(address)
									#content = instruction.dcache[1][1][index][1]	
									#instruction.registers[int(self.code[1][1:])] = content
									instruction.lru_block_one = 0
							elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
								self.dcacheldhitstracker[goodstuff] = 0
								if addresses_in_first_cache == [None, None, None, None]:		
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0, 4):
										instruction.dcache[0][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]	
									instruction.lru_block_one = 1
								elif addresses_in_second_cache == [None, None , None, None]:	
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0,4):
										instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]		
									instruction.lru_block_one = 0
								elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:	
									if lru_block_one == 0:
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instruction.dcache[0][1]
										for i in range(0, 4):
											instruction.dcache[0][1][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
										#Writing back regardless	
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setzero_block_one_dirty == 1:
											self.lddirtytracker[goodstuff] = 1
											instruction.dcache_setzero_block_one_dirty = 0
										instruction.lru_block_one = 1
									elif lru_block_one == 1:
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instrucion.dcache[1][1]
										for i in range(0, 4):
											instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]			
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setone_block_one_dirty == 1:
											self.lddirtytracker[goodstuff] = 1
											instruction.dcache_setone_block_one_dirty = 0
										instruction.lru_block_one = 0
					#print self.dcacheldhitstracker
					#print self.lddirtytracker
					if self.dcacheldhitstracker[0] == 1:
						self.ldonecachelatency = instruction.dcache_latency
						self.ldonememlatency = 0
						self.ldstagetwo = True
					elif self.dcacheldhitstracker[0] == 0:
						self.ldonecachelatency = 0
						self.ldstageone = True
						if self.lddirtytracker[0] == 0:
							self.ldonememlatency = 2 * (instruction.dcache_latency + instruction.mainmemory_latency)

						elif self.lddirtytracker[0] == 1:
							self.ldonememlatency = 4 * (instruction.dcache_latency + instruction.mainmemory_latency)

					if self.dcacheldhitstracker[1] == 1:
						self.ldtwocachelatency = instruction.dcache_latency
						self.ldtwomemlatency = 0
						self.ldstagefour = True
					elif self.dcacheldhitstracker[1] == 0:
						self.ldtwocachelatency = 0
						self.ldstagethree = True
						if self.lddirtytracker[1] == 0:
							self.ldtwomemlatency = 2 * (instruction.dcache_latency + instruction.mainmemory_latency)
						elif self.lddirtytracker[1] == 1:
							self.ldtwomemlatency = 4 * (instruction.dcache_latency + instruction.mainmemory_latency)				

					#print "-----------------------LOAD REPORT------------------"		
					#print 	self.ldonecachelatency
					#print 	self.ldonememlatency
					#print 	self.ldtwocachelatency
					#print 	self.ldtwomemlatency
					#print "---------------------------------------------------"	



				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.mem == False and self.memdone == False) or (self.uidone == True and instruction.mem == True 
					and instruction.memsetter == num and self.memdone == False)):
					instruction.memsetter = num
					instruction.mem = True
					if self.ldstageone == False:
						self.ldonecachelatency = self.ldonecachelatency - 1
						if self.ldonecachelatency == 0:
							self.ldstageone = True
					elif self.ldstagetwo == False:		
						if (instruction.maindatabus_busy == False  and instruction.instructionbusrequest == False) or (instruction.maindatabus_busy == True and instruction.databussetter == num):
							instruction.maindatabus_busy = True
							instruction.databussetter = num
							self.ldonememlatency = self.ldonememlatency - 1
							if self.ldonememlatency == 0:
								#self.execstage = True
								self.setdatabusfalse = 1
								self.ldstagetwo = True
								#self.setmemfalse = 1
								#self.memdone = True
					elif self.ldstagethree == False:
						self.ldtwocachelatency  = self.ldtwocachelatency - 1
						if self.ldtwocachelatency == 0:
							self.ldstagethree = True
							if self.ldstagefour == True:
								self.execstage = True
								self.setdatabusfalse = 1
								self.ldstagefour = True
								self.setmemfalse = 1
								self.memdone = True			
					elif self.ldstagefour == False:
						if (instruction.maindatabus_busy == False  and instruction.instructionbusrequest == False) or (instruction.maindatabus_busy == True and instruction.databussetter == num):
							instruction.maindatabus_busy = True
							instruction.databussetter = num
							self.ldtwomemlatency = self.ldtwomemlatency - 1
							if self.ldtwomemlatency == 0:
								self.execstage = True
								self.setdatabusfalse = 1
								self.ldstagefour = True
								self.setmemfalse = 1
								self.memdone = True

				elif self.uidone == True and instruction.mem == True and instruction.memsetter != num and self.memdone == False:
					self.hazards[3] = "Y"

			





			elif self.code[0] == "s.d":
				if self.uidone == False and instruction.mainui_busy == False:
					self.result[1] = counter - 1
					instruction.mainui_busy = True
					instruction.uisetter = num
					self.setuifalse = 1
					self.uidone = True
					#FINDING THE ADDRESSES IN LOAD DOUBLE WORD. BOTH ADDRESSSES ARE FOUND AND STORED IN AN ARRAY WITH CORRESPONDING BITS:
					if "(" in self.code[2]:
						block_bits = []
						addresses_array = []
						#lw r1 4(r10)
						#lw r2 4(r3)
						address_one = int(self.code[2].split("(")[0]) + instruction.registers[int(re.search("\((\w\d+)\)", self.code[2]).group(1)[1:])]
						if address_one in instruction.zero_block:
							block_bits.append(0)
						elif address_one in instruction.one_block:
							block_bits.append(1)	
						address_two = address_one + 4
						if address_two in instruction.zero_block:
							block_bits.append(0)
						elif address_two in instruction.one_block:
							block_bits.append(1)
						addresses_array.append(address_one)
						addresses_array.append(address_two)
						#instruction.registers[self.code[]]
					elif "(" not in self.code[2]:
						block_bits = []
						addresses_array = []
						#lw r1 r21
						#lw r1 r21
						address_one = int(instruction.registers[int(self.code[2][1:])])
						if address_one in instruction.zero_block:
							block_bits.append(0)
						elif address_one in instruction.one_block:
							block_bits.append(1)
						address_two = address_one + 4
						if address_two in instruction.zero_block:
							block_bits.append(0)
						elif address_two in instruction.one_block:
							block_bits.append(1)
						addresses_array.append(address_one)
						addresses_array.append(address_two)

					#print "**********************PRINTING BLOCK BITS*********************************"
					#print block_bits
					#print "**************************************************************************"
					#print "*************************PRINTING ADDRESSES*******************************"
					#print addresses_array
					#print "**************************************************************************"		
					for goodstuff in range(len(addresses_array)):
						address = addresses_array[goodstuff]
						bit = block_bits[goodstuff]
						if bit == 0:
							instruction.datacachemaincount += 1
							addresses_in_first_cache = [x[0] for x in instruction.dcache[0][0]]
							addresses_in_second_cache = [y[0] for y in instruction.dcache[1][0]]
							if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
								instruction.datacachehitcount += 1
								#print self.dcacheldhitstracker
								self.dcacheldhitstracker[goodstuff] = 1 #SIGNIFIES A CACHE HIT
								if address in addresses_in_first_cache:
									index = addresses_in_first_cache.index(address)
									#THE BELOW LINE SHOULD NEVER BE UNCOMMENTED
									#content = instruction.dcache[0][0][index][1]
									#instruction.registers[int(self.code[1][1:])] = content
									#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
									instruction.dcache_setzero_block_zero_dirty = 1
									instruction.lru_block_zero = 1
								elif address in addresses_in_second_cache:
									index = addresses_in_second_cache.index(address)
									#content = instruction.dcache[1][0][index][1]
									#THE BELOW LINW SHOULD NEVER BE UNCOMMENTED SINCE THIS IS L.D
									#instruction.registers[int(self.code[1][1:])] = content
									instruction.dcache_setone_block_zero_dirty = 1
									instruction.lru_block_zero = 0 	
							elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
								self.dcacheldhitstracker[goodstuff] = 0
								if addresses_in_first_cache == [None, None, None, None]:
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0, 4):
										instruction.dcache[0][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
									instruction.dcache_setzero_block_zero_dirty = 1		
									instruction.lru_block_zero = 1	
								elif addresses_in_second_cache == [None, None, None, None]:	
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0,4):
										instruction.dcache[1][0][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
									instruction.dcache_setone_block_zero_dirty = 1		
									instruction.lru_block_zero = 0	

								elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:
									if lru_block_zero == 0:
										#REPLACE BLOCK 0 OF SET ZERO. 
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instruction.dcache[0][0]
										for i in range(0, 4):
											instruction.dcache[0][0][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
										#Writing back regardless	
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setzero_block_zero_dirty == 1:
											self.lddirtytracker[goodstuff]= 1
											instruction.dcache_setzero_block_zero_dirty = 0
										instruction.dcache_setzero_block_zero_dirty = 1	
										instruction.lru_block_zero = 1
									elif lru_block_zero == 1:
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instruction.dcache[1][0]
										for i in range(0, 4):
											instruction.dcache[1][0][i]	= [temp_holder[i], instruction.memdata[temp_holder[i]]]
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setone_block_zero_dirty == 1:
											self.lddirtytracker[goodstuff] = 1
											instruction.dcache_setone_block_zero_dirty = 0
										instruction.dcache_setone_block_zero_dirty = 1	
										instruction.lru_block_zero = 0							




						elif bit == 1:
							instruction.datacachemaincount += 1	
							addresses_in_first_cache = [x[0] for x in instruction.dcache[0][1]]
							addresses_in_second_cache = [y[0] for y in instruction.dcache[1][1]]
							if(address in addresses_in_first_cache) or (address in addresses_in_second_cache):
								instruction.datacachehitcount += 1
								self.dcacheldhitstracker[goodstuff] = 1 #SIGNIFIES A CACHE HIT
								if address in addresses_in_first_cache:
									index = addresses_in_first_cache.index(address)
									#content = instruction.dcache[0][1][index][1]
									#instruction.registers[int(self.code[1][1:])] = content
									#SET NEW LRU COUNT FOR THE IMP:::::::FIRST BLOCK OF SECOND CACHE
									instruction.dcache_setzero_block_one_dirty = 1
									instruction.lru_block_one = 1
								elif address in addresses_in_second_cache:
									index = addresses_in_second_cache.index(address)
									#content = instruction.dcache[1][1][index][1]	
									#instruction.registers[int(self.code[1][1:])] = content
									instruction.dcache_setone_block_one_dirty = 1
									instruction.lru_block_one = 0
							elif (address not in addresses_in_first_cache) and (address not in addresses_in_second_cache):
								self.dcacheldhitstracker[goodstuff] = 0
								if addresses_in_first_cache == [None, None, None, None]:		
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0, 4):
										instruction.dcache[0][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
									instruction.dcache_setzero_block_one_dirty = 1		
									instruction.lru_block_one = 1
								elif addresses_in_second_cache == [None, None , None, None]:	
									for i in instruction.memblocks:
										if address in i:
											temp_holder = i
											break
									for i in range(0,4):
										instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]
									instruction.dcache_setone_block_one_dirty = 1			
									instruction.lru_block_one = 0
								elif addresses_in_first_cache != [None, None, None, None] and addresses_in_second_cache != [None, None, None, None]:	
									if lru_block_one == 0:
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instruction.dcache[0][1]
										for i in range(0, 4):
											instruction.dcache[0][1][i]	 = [temp_holder[i], instruction.memdata[temp_holder[i]]]
										#Writing back regardless	
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setzero_block_one_dirty == 1:
											self.lddirtytracker[goodstuff] = 1
											instruction.dcache_setzero_block_one_dirty = 0
										instruction.dcache_setzero_block_one_dirty = 1	
										instruction.lru_block_one = 1
									elif lru_block_one == 1:
										for i in instruction.memblocks:
											if address in i:
												temp_holder = i
												break
										temp_holder_two = instrucion.dcache[1][1]
										for i in range(0, 4):
											instruction.dcache[1][1][i] = [temp_holder[i], instruction.memdata[temp_holder[i]]]			
										for i in temp_holder_two:
											instruction.memdata[i[0]] = i[1]
										if instruction.dcache_setone_block_one_dirty == 1:
											self.lddirtytracker[goodstuff] = 1
											instruction.dcache_setone_block_one_dirty = 0
										instruction.dcache_setone_block_one_dirty = 1	
										instruction.lru_block_one = 0
					#print self.dcacheldhitstracker
					#print self.lddirtytracker
					if self.dcacheldhitstracker[0] == 1:
						self.ldonecachelatency = instruction.dcache_latency
						self.ldonememlatency = 0
						self.ldstagetwo = True
					elif self.dcacheldhitstracker[0] == 0:
						self.ldonecachelatency = 0
						self.ldstageone = True
						if self.lddirtytracker[0] == 0:
							self.ldonememlatency = 2 * (instruction.dcache_latency + instruction.mainmemory_latency)

						elif self.lddirtytracker[0] == 1:
							self.ldonememlatency = 4 * (instruction.dcache_latency + instruction.mainmemory_latency)

					if self.dcacheldhitstracker[1] == 1:
						self.ldtwocachelatency = instruction.dcache_latency
						self.ldtwomemlatency = 0
						self.ldstagefour = True
					elif self.dcacheldhitstracker[1] == 0:
						self.ldtwocachelatency = 0
						self.ldstagethree = True
						if self.lddirtytracker[1] == 0:
							self.ldtwomemlatency = 2 * (instruction.dcache_latency + instruction.mainmemory_latency)
						elif self.lddirtytracker[1] == 1:
							self.ldtwomemlatency = 4 * (instruction.dcache_latency + instruction.mainmemory_latency)				

					#print "-----------------------LOAD REPORT------------------"		
					#print 	self.ldonecachelatency
					#print 	self.ldonememlatency
					#print 	self.ldtwocachelatency
					#print 	self.ldtwomemlatency
					#print "---------------------------------------------------"	



				elif self.uidone == False and instruction.mainui_busy == True:
					self.hazards[3] = "Y"	
				elif((self.uidone == True and instruction.mem == False and self.memdone == False) or (self.uidone == True and instruction.mem == True 
					and instruction.memsetter == num and self.memdone == False)):
					instruction.memsetter = num
					instruction.mem = True
					if self.ldstageone == False:
						self.ldonecachelatency = self.ldonecachelatency - 1
						if self.ldonecachelatency == 0:
							self.ldstageone = True
					elif self.ldstagetwo == False:		
						if (instruction.maindatabus_busy == False  and instruction.instructionbusrequest == False) or (instruction.maindatabus_busy == True and instruction.databussetter == num):
							instruction.maindatabus_busy = True
							instruction.databussetter = num
							self.ldonememlatency = self.ldonememlatency - 1
							if self.ldonememlatency == 0:
								#self.execstage = True
								self.setdatabusfalse = 1
								self.ldstagetwo = True
								#self.setmemfalse = 1
								#self.memdone = True
					elif self.ldstagethree == False:
						self.ldtwocachelatency  = self.ldtwocachelatency - 1
						if self.ldtwocachelatency == 0:
							self.ldstagethree = True
							if self.ldstagefour == True:
								self.execstage = True
								self.setdatabusfalse = 1
								self.ldstagefour = True
								self.setmemfalse = 1
								self.memdone = True			
					elif self.ldstagefour == False:
						if (instruction.maindatabus_busy == False  and instruction.instructionbusrequest == False) or (instruction.maindatabus_busy == True and instruction.databussetter == num):
							instruction.maindatabus_busy = True
							instruction.databussetter = num
							self.ldtwomemlatency = self.ldtwomemlatency - 1
							if self.ldtwomemlatency == 0:
								self.execstage = True
								self.setdatabusfalse = 1
								self.ldstagefour = True
								self.setmemfalse = 1
								self.memdone = True

				elif self.uidone == True and instruction.mem == True and instruction.memsetter != num and self.memdone == False:
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
				elif((self.uidone == True and instruction.mem == False and self.memdone == False and instruction.instructionbusrequest == False)):
					instruction.memsetter = num
					instruction.mem = True
					self.execstage = True
					self.setmemfalse = 1
					#THE ACTUAL LOGIC FOR ADDITION
					if self.code[0] == "dadd":
						answer = instruction.registers[int(self.code[2][1:])] + instruction.registers[int(self.code[3][1:])]
						regindex = int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "daddi":
						answer = instruction.registers[int(self.code[2][1:])] + int(self.code[3])
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
				elif((self.uidone == True and instruction.mem == False and self.memdone == False and instruction.instructionbusrequest == False)):
					instruction.memsetter = num
					instruction.mem = True
					self.execstage = True
					self.setmemfalse = 1
					#THE ACTUAL LOGIC FOR ADDITION
					if self.code[0] == "dsub":
						answer = instruction.registers[int(self.code[2][1:])] - instruction.registers[int(self.code[3][1:])]
						regindex = int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "dsubi":
						answer = instruction.registers[int(self.code[2][1:])] - int(self.code[3])
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

				elif((self.uidone == True and instruction.mem == False and self.memdone == False and instruction.instructionbusrequest == False)):
					instruction.memsetter = num
					instruction.mem = True
					self.execstage = True
					self.setmemfalse = 1
					"""ACTUAL BITWISE ANDING"""
					if self.code[0] == "and":
						answer = instruction.registers[int(self.code[2][1:])] & instruction.registers[int(self.code[3][1:])]
						regindex = 	int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "andi":
						answer = instruction.registers[int(self.code[2][1:])] & int(self.code[3][1:])
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
				elif((self.uidone == True and instruction.mem == False and self.memdone == False and instruction.instructionbusrequest == False)):
					instruction.memsetter = num
					instruction.mem = True
					self.execstage = True
					self.setmemfalse = 1
					"""ACTUAL BITWISE ORING"""
					if self.code[0] == "or":
						answer = instruction.registers[int(self.code[2][1:])] | instruction.registers[int(self.code[3][1:])]
						regindex = 	int(self.code[1][1:])
						instruction.registers[regindex] = answer
					elif self.code[0] == "ori":
						answer = instruction.registers[int(self.code[2][1:])] | int(self.code[3][1:])
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
			#print "Entered WriteBack"
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
	for cachecounter in range(0, 16):
		instruction.instruction_cache.append([None, [cachecounter, cachecounter + 16, cachecounter + 32, cachecounter + 48]])	
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
	#print "Now making destination dict"
	destdict =  destination_op_finder.dest_op_finder(parsed_code, labels)
	#print destdict
	#print "Destination dict made"
	#<-----------TESTING ROUTINE---------------------->
	#for i in destdict.items():
	#	print i
	#<------------------------------------------------>
	#FINDS RAW DEPENDENCIES
	#print "Now making raw dict"
	raw_dict = raw_finder.raw_finder(parsed_code, destdict, labels)
	#print "Raw dict made"
	#THE RAW FINDER RETURNS NO ENTRIES CORRESPONDING TO THOSE WHICH HAVE NO DEPENDENCIES. ADDING NONE FOR SUCH CASE
	for i in range(0, len(parsed_code)):
		if i in raw_dict.keys():
			pass
		else:
			raw_dict[i] = None
	#print raw_dict		
	instruction.registers = [int(x.strip(), 2) for x in (open(sys.argv[3], r"U")).readlines()]
	#<------TESTING MODULE----------------->
	#for i in register_data:
	#	print i	
	temporary_memdata = [int(x.strip(), 2) for x in (open(sys.argv[2], r"U")).readlines()]
	mem_index = []
	for i in range(0,len(temporary_memdata)):
		mem_index.append(256 + i * 4)
	instruction.memdata = dict(zip(mem_index, temporary_memdata))
	temporary_blocker = []
	blockercounter = 0
	for i in range(0, 32):
		if blockercounter != 4:
			temporary_blocker.append(256 + i * 4)
			blockercounter = blockercounter + 1
		if blockercounter == 4:
			instruction.memblocks.append(temporary_blocker)
			temporary_blocker = []
			blockercounter = 0

	#INITIALIZING THE DATA CACHE
	for something in range(0, 2):
		set  = []
		for nice in range(0, 2):
			block = []
			for just in range(0, 4):
				block.append([None, None])
			set.append(block)
		instruction.dcache.append(set)
	marker = 0
	for i in range(256, 381, 4):
		if marker < 4:
			instruction.zero_block.append(i)
			marker = marker + 1
		elif marker >= 4:
			marker = marker + 1
			instruction.one_block.append(i)
			if marker == 8:
				marker = 0	
	#print "----------------------"
	#print instruction.zero_block
	#print "----------------------"
	#print instruction.one_block	
	#print "----------------------"				
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
	#print raw_dict[10]
	#print instruction.registers
	counter = 1
	#while(obj_list[-1].result[0] == None):
	#print instruction.instruction_cache
	#while(obj_list[-1].result[0] == None):
	while(counter < 10000):
		#print "Entered while"
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
		if obj_list[instruction.memsetter].setmemfalse == 1:
			instruction.mem = False
		counter = counter + 1
		#print counter
		#print int(instruction.registers[4], 2)
		#if counter == 10:
		#	break
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
	#for i in obj_list:
	#	print i.result,
	#	print i.hazards
	#	print "------------"
	#print instruction.instruction_cache
	print instruction.instructioncachemaincount
	print instruction.instructioncachehitcount
	print "************************************************"
	print instruction.datacachemaincount
	print instruction.datacachehitcount
	print "************************************************"
	for i in obj_list:
		print i.result
	print "***********************************"
	print "**** Writing Results to file ******"
	print "***********************************"
	result = open(sys.argv[5], "w")
	for i in obj_list:
		result.write(" ".join([str(x) for x in i.result]))
		result.write("   					")
		result.write(" ".join([str(x) for x in i.hazards]))
		result.write("\n")	
	result.write("The number of instruction cache access are" + str(instruction.instructioncachemaincount) + "\n")
	result.write("The number of instruction cache hits are " + str(instruction.instructioncachehitcount) + "\n")
	result.write("The number of data cache access are " + str(instruction.datacachemaincount) + "\n")
	result.write("The number of data cache hits are" + str(instruction.datacachehitcount) + "\n")
	result.close()	
	#print instruction.memdata
	#print len(instruction.memdata)
	#print instruction.memblocks	
	#print instruction.dcache
	#print instruction.zero_block
	#print "****************************************"
	#print instruction.one_block
	#print "****************************************"
if __name__ == "__main__":
	main()

