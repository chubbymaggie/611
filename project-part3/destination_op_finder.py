def dest_op_finder(parsed_code, labels):
	valid_ops = ["lw", "sw", "l.d", "s.d", "dadd", "daddi", "dsub", "dsubi", "and", "andi", "or", "ori", "add.d", "sub.d", "mul.d", "div.d", "j", "bne", "beq", "hlt"]
	#Destination registers before my line number
	dregs = {}
	 
	for i in range(0, len(parsed_code)):
		if parsed_code[i][0] in valid_ops:
			if(parsed_code[i][0] == "lw")or(parsed_code[i][0] == "l.d"):
				dregs[i] = parsed_code[i][1]
			elif (parsed_code[i][0] == "sw")or(parsed_code[i][0] == "s.d"):
				dregs[i] = None
			elif (parsed_code[i][0] == "dadd") or(parsed_code[i][0] == "daddi") or  (parsed_code[i][0] == "add.d"):
				dregs[i] = parsed_code[i][1]
			elif (parsed_code[i][0] == "dsub") or  (parsed_code[i][0] == "dsubi") or (parsed_code[i][0] == "sub.d"):
				dregs[i] = parsed_code[i][1]
			elif (parsed_code[i][0] == "mul.d") or (parsed_code[i][0] == "div.d"):
				dregs[i] = parsed_code[i][1]
			elif (parsed_code[i][0] == "and") or (parsed_code[i][0] == "andi") or (parsed_code[i][0] == "or") or (parsed_code[i][0] == "ori"):
				dregs[i] = parsed_code[i][1]
			elif (parsed_code[i][0] == "j") or (parsed_code[i][0] == "bne") or (parsed_code[i][0] == "beq") or (parsed_code[i][0] == "hlt"):
				dregs[i] = None
		
		elif parsed_code[i][0] in labels:
				
			if(parsed_code[i][1] == "lw")or(parsed_code[i][1] == "l.d"):
				dregs[i] = parsed_code[i][2]
			elif (parsed_code[i][1] == "sw")or(parsed_code[i][1] == "s.d"):
				dregs[i] = None
			elif (parsed_code[i][1] == "dadd") or(parsed_code[i][1] == "daddi") or  (parsed_code[i][1] == "add.d"):
				dregs[i] = parsed_code[i][2]
			elif (parsed_code[i][1] == "dsub") or  (parsed_code[i][1] == "dsubi") or (parsed_code[i][1] == "sub.d"):
				dregs[i] = parsed_code[i][2]
			elif (parsed_code[i][1] == "mul.d") or (parsed_code[i][1] == "div.d"):
				dregs[i] = parsed_code[i][2]
			elif (parsed_code[i][1] == "and") or (parsed_code[i][1] == "andi") or (parsed_code[i][1] == "or") or (parsed_code[i][1] == "ori"):
				dregs[i] = parsed_code[i][2]
			elif (parsed_code[i][1] == "j") or (parsed_code[i][1] == "bne") or (parsed_code[i][1] == "beq") or (parsed_code[i][1] == "hlt"):
				dregs[i] = None
	return dregs
