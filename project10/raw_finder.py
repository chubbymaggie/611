import re
def raw_finder(parsed_code, destdict, labels):
	#print destdict
	raw_dict = {0 : None}
	valid_ops = ["lw", "sw", "l.d", "s.d", "dadd", "daddi", "dsub", "dsubi", "and", "andi", "or", "ori", "add.d", "sub.d", "mul.d", "div.d", "j", "bne", "beq", "hlt"]
	for i in range(0, len(parsed_code)):
		if parsed_code[i][0] in valid_ops:
			#if it is add keep a track of which instructions have it's operands in its destination folder
			if(parsed_code[i][0] == "add") or (parsed_code[i][0] == "addi") or (parsed_code[i][0] == "add.d"):
				counter = i - 1	
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter])or(parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)			
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1	
			elif (parsed_code[i][0] == "sub") or (parsed_code[i][0] == "subi") or (parsed_code[i][0]== "sub.d"):
				counter = i - 1	
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter])or(parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)			
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1

			elif (parsed_code[i][0] == "mul.d") or (parsed_code[i][0] == "div.d"):
				counter = i - 1	
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter])or(parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)			
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1

			elif (parsed_code[i][0] == "and") or (parsed_code[i][0] == "andi") or (parsed_code[i][0] == "or") or (parsed_code[i][0] == "ori"):
				counter = i - 1
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter]) or (parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1		
					else:			
						counter = counter - 1
			elif (parsed_code[i][0] == "lw") or (parsed_code[i][0] == "l.d"):
				counter = i - 1
				if "(" in parsed_code[i][-1]:
					match = re.search(r"\((\w\d+)\)", parsed_code[i][-1])
					tempreg = match.group(1)
				else:
					tempreg = parsed_code[i][-1]
				while(counter >= 0):
					if destdict[counter] != None:
						if (tempreg in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [coutner]
						counter = counter - 1
					else:
						counter = counter - 1	

			elif (parsed_code[i][0] == "sw") or (parsed_code[i][0] == "s.d"):
				counter = i - 1
				if "(" in parsed_code[i][-1]:
					match = re.search(r"\((\w\d+)\)", parsed_code[i][-1])
					tempreg_one = match.group(1)
				else:
					tempreg_one = parsed_code[i][-1]
				if "(" in parsed_code[i][-2]:
					match = re.search(r"\((\w\d+)\)", parsed_code[i][-2])
					tempreg_two = match.group(1)
				else:
					tempreg_two = parsed_code[i][-2]
				while(counter >= 0):
					if destdict[counter] != None:
						if (tempreg_one in destdict[counter]) or (tempreg_two in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [coutner]
						counter = counter - 1
					else:
						counter = counter - 1	
			elif (parsed_code[i][0] == "j") or (parsed_code[i][0] == "hlt"):
				try:
					temp = raw_dict[i]
					if temp != None:
						temp = None
				except:
					raw_dict[i] = None
			elif(parsed_code[i][0] == "beq") or (parsed_code[i][0] == "bnq" or (parsed_code[i][0] == "bne")):
				counter = i - 1
				while(counter >= 0):
					if destdict[counter] != None:
						if (parsed_code[i][-2] in destdict[counter]) or (parsed_code[i][-3] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1

		elif parsed_code[i][0] in labels:
			#if it is add keep a track of which instructions have it's operands in its destination folder
			if(parsed_code[i][1] == "add") or (parsed_code[i][1] == "addi") or (parsed_code[i][1] == "add.d"):
				counter = i - 1	
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter])or(parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)			
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1	
			elif (parsed_code[i][1] == "sub") or (parsed_code[i][1] == "subi") or (parsed_code[i][1]== "sub.d"):
				counter = i - 1	
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter])or(parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)			
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1	
			elif (parsed_code[i][1] == "mul.d") or (parsed_code[i][1] == "div.d"):
				counter = i - 1	
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter])or(parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)			
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1

			elif (parsed_code[i][1] == "and") or (parsed_code[i][1] == "andi") or (parsed_code[i][1] == "or") or (parsed_code[i][1] == "ori"):
				counter = i - 1
				while(counter >= 0):
					if destdict[counter] != None:
						if(parsed_code[i][-1] in destdict[counter]) or (parsed_code[i][-2] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]
						counter = counter - 1
					else:
						counter = counter - 1	


			elif (parsed_code[i][1] == "lw") or (parsed_code[i][1] == "l.d"):
				counter = i - 1
				if "(" in parsed_code[i][-1]:
					match = re.search(r"\((\w\d+)\)", parsed_code[i][-1])
					tempreg = match.group(1)
				else:
					tempreg = parsed_code[i][-1]
				while(counter >= 0):
					if destdict[counter] != None:
						if (tempreg in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [coutner]

						counter = counter - 1
					else:
						counter = counter - 1

			elif (parsed_code[i][1] == "sw") or (parsed_code[i][1] == "s.d"):
				counter = i - 1
				if "(" in parsed_code[i][-1]:
					match = re.search(r"\((\w\d+)\)", parsed_code[i][-1])
					tempreg_one = match.group(1)
				else:
					tempreg_one = parsed_code[i][-1]
				if "(" in parsed_code[i][-2]:
					match = re.search(r"\((\w\d+)\)", parsed_code[i][-2])
					tempreg_two = match.group(1)
				else:
					tempreg_two = parsed_code[i][-2]
				while(counter >= 0):
					if destdict[counter] != None:
						if (tempreg_one in destdict[counter]) or (tempreg_two in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [coutner]
						counter = counter - 1
					else:
						counter = counter - 1	
			elif (parsed_code[i][1] == "j") or (parsed_code[i][1] == "hlt"):
				try:
					temp = raw_dict[i]
					if temp != None:
						temp = None
				except:
					raw_dict[i] = None
			elif(parsed_code[i][1] == "beq") or (parsed_code[i][1] == "bnq") or (parsed_code[i][0] == "bne"):
				counter = i - 1
				while(counter >= 0):
					if destdict[counter] != None:
						if (parsed_code[i][-2] in destdict[counter]) or (parsed_code[i][-3] in destdict[counter]):
							try:
								temp = raw_dict[i]
								temp.append(counter)
								raw_dict[i] = temp
							except:
								raw_dict[i] = [counter]	
						counter = counter - 1
					else:
						counter = counter - 1	
	return raw_dict
