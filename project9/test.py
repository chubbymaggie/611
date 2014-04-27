#counter = 1
#temp = [[0, 0], [1, 0], [2 ,0], [3, 0]]
#while(temp[-1][1] < 10):
#	for i in range(0, len(temp)):
#		temp[i][1] += 1
#	if counter == 5:
#		temp.extend([[4,0], [5, 0]])
#	print temp
#	counter = counter  + 1
zeros = []
ones = []
flag = 0
for i in range(256, 381, 4):
	if flag < 4:
		zeros.append(i)
		flag = flag + 1
	elif flag >= 4:
		flag = flag + 1
		ones.append(i)
		if flag == 8:
			flag = 0
				
print zeros
print ones	
