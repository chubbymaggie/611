#!/usr/bin/python
import re
def war_finder(parsed_code, destdict, labels):
	war_dict = {}
	labels = [] if labels is None else labels
	for i in range(0, len(parsed_code)):
		if destdict[i] != None:
			counter = i - 1
			while(counter >= 0):
				if parsed_code[counter][0] not in labels:
					if parsed_code[counter][0] in ["dadd", "daddi", "add.d", "dsub", "dsubi", "sub.d", "mul.d", "div.d", "and", "andi", "or", "ori"]:
						if destdict[i] in [parsed_code[counter][-1], parsed_code[counter][-2]]:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = [counter]
					elif parsed_code[counter][0] in ["lw", "l.d"]:
						if "(" in parsed_code[counter][-1]:
							match = re.search(r"\((\w\d+)\)", parsed_code[counter][-1])	
							temp_reg = match.group(1)
						else:
							temp_reg = parsed_code[counter][-1]
						if destdict[i] == temp_reg:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = [counter]
					elif parsed_code[counter][0] in ["sw", "s.d"]:
						if "(" in parsed_code[counter][-1]:
							match = re.search(r"\((\w\d+)\)", parsed_code[counter][-1])
							temp_regone = match.group(1)
						else:
							temp_regone = parsed_code[counter][-1]
						if "(" in parsed_code[counter][-2]:
							match = re.search(r"\((\w\d+)\)", parsed_code[counter][-2])
						else:
							temp_regtwo = parsed_code[counter][-2]
						
						if destdict[i] in [temp_regone, temp_regtwo]:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = [counter]
					elif parsed_code[counter][0] in ["bne", "bnq"]:
						if destdict[i] in [parsed_code[counter][-2], parsed_code[counter][-3]]:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = counter							
					elif parsed_code[counter][0] in ["hlt"]:
						pass		
					counter = counter - 1
				elif parsed_code[counter][0] in labels:
					if parsed_code[counter][1] in ["dadd", "daddi", "add.d", "dsub", "dsubi", "sub.d", "mul.d", "div.d", "and", "andi", "or", "ori"]:
						if destdict[i] in [parsed_code[counter][-1], parsed_code[counter][-2]]:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = [counter]
					elif parsed_code[counter][1] in ["lw", "l.d"]:
						if "(" in parsed_code[counter][-1]:
							match = re.search(r"\((\w\d+)\)", parsed_code[counter][-1])	
							temp_reg = match.group(1)
						else:
							temp_reg = parsed_code[counter][-1]
						if destdict[i] == temp_reg:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = [counter]
					elif parsed_code[counter][1] in ["sw", "s.d"]:
						if "(" in parsed_code[counter][-1]:
							match = re.search(r"\((\w\d+)\)", parsed_code[counter][-1])
							temp_regone = match.group(1)
						else:
							temp_regone = parsed_code[counter][-1]
						if "(" in parsed_code[counter][-2]:
							match = re.search(r"\((\w\d+)\)", parsed_code[counter][-2])
						else:
							temp_regtwo = parsed_code[counter][-2]
						
						if destdict[i] in [temp_regone, temp_regtwo]:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = [counter]
					elif parsed_code[counter][1] in ["bne", "bnq"]:
						if destdict[i] in [parsed_code[counter][-2], parsed_code[counter][-3]]:
							try:
								temp = war_dict[i]
								temp.append(counter)
								war_dict[i] = temp
							except:
								war_dict[i] = [counter]					
					elif parsed_code[counter][0] in ["hlt"]:
						pass		
					counter = counter - 1
	return war_dict
