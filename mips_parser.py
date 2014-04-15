#!/usr/bin/python
import sys
import re
"""The intention of this function is to parse input mips code from the file inst.txt in the main
The input will be a list of all lines present in the file with a newline character at the end. I will write the function to parse the mips code and make sure everythin is fine."""
def mips_parse(code):
	return_list = []
	validoperands = {"lw": 2, "sw": 2, "l.d":
	2, "s.d": 2, "dadd": 3, "daddi":
	3, "dsub":
	3, "dsubi": 3, "and": 3, "andi":
	3, "or":3, "ori":3, "add.d":3, "sub.d":3, "mul.d":3, "div.d":3, "j":1, "bne":3, "beq": 3, "hlt":1 }
	#If there are spances in between input lines in the input file
	for i in range(0, len(code)):
		if code[i] == "\n":
			del code[i]
			

#The last two lines of the code have to be halt
	if (code[-1].strip().lower() == "hlt") and (code[-2].strip().lower() == "hlt"):
		pass
	else:
		print "The last two lines of the input MIPS code need to be a HLT statement, please fix that and run the simulator again"
		sys.exit(1)

	#Break everything on white spaces first
	#Check if its a jump statement by looking at : in the first word.
	#if its not a jump statement, then check if its a valid MIPS instruction that was presented.Check if they are a valid MIPS keyword only for the first element if its not a jump instruction. 
	#if "," are present strip them

	"""Since the amount of whitespacing actually doesnot matter and splitting on commas isnt really an option since I wont be able to split the string equally, I have to work with the entire string in general and make sure that the splitting is done properly"""
	labels = []
	for line in code:
		#print line
		flag = 0
		jump_flag = 0
		#Get rid of the newline charecter
		line = line.lower().strip() 
		#look for branch statements. Each branch statement must have a : in it
		if ":" in line:
			#JUMP Instruction
			line = line.split(":")		
			jump_flag = 1
			rest = line[1]
			labels.append(line[0])	
		else:
			rest = line
			#Figure out what operation it is
		operator_list = []
		for i in validoperands.keys():
			if i in rest:
				operator_list.append(i)
				flag = 1
		operator_list = sorted(operator_list, key = lambda x: len(x), reverse = True)
		operator = operator_list[0]
		#If no operand is found in the line1 part, flag remains 1
		if flag == 0:
			print "No valid operand found"
			sys.exit(1)
		#Get rid of the operator
		instr = rest.replace(operator, "")
		#get rid of all white spaces and do a pure split on commas
		instr = (instr.replace(" ", "")).split(",")
		#print instr
		if len(instr) != validoperands[operator]:
			print "Not enough operands provided for " + operator
			sys.exit(1)
		#Append the jump label to code_line
		code_line = []
		if jump_flag == 1:
		#Adding the jump label if the jump flag is set.
			code_line.append(line[0])
		#Append operator to code line
		code_line.append(operator)
		match_register = re.compile(r"[fr](\d+)")
		for code_element in instr:
			#Checking if all register values are from 0  to 31 only
			match = match_register.search(code_element)
			if match:
				if int(match.group(1)) > 31:
					print "Register value grater than total number of registers"
					sys.exit(1)
			if code_element != "":
				code_line.append(code_element)		
		#print code_line
		return_list.append(code_line)
	if labels:
		return return_list, labels
	else:
		return return_list, None	

#def main():
#	filename = open(sys.argv[1], r"U")
#	code = filename.readlines()
#	parsed_code, labels = mips_parse(code)
#	for line in parsed_code:
#		print line
#
#	print "---------------------------"
#	print labels		

#if __name__ == "__main__":
#	main()
