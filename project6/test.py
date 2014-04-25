counter = 1
temp = [[0, 0], [1, 0], [2 ,0], [3, 0]]
while(temp[-1][1] < 10):
	for i in range(0, len(temp)):
		temp[i][1] += 1
	if counter == 5:
		temp.extend([[4,0], [5, 0]])
	print temp
	counter = counter  + 1

	
	
