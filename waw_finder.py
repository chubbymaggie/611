def waw_finder(parsed_code, destdict, labels):
	destdictrev = sorted(destdict.items(), key = lambda x:x[0], reverse = True)
	waw_dict = {}
	for i in range(0, len(destdictrev)):
		elem = destdictrev[i]
		if elem[1] != None:
			for j in range(i + 1, len(destdictrev)):
				if destdictrev[j][1] != None:
					if destdictrev[j][1] == elem[1]:
						try:
							temp = waw_dict[elem[0]]
							temp.append(destdictrev[j][0])
							waw_dict[elem[0]] = temp
						except:
							waw_dict[elem[0]] = [destdictrev[j][0]]
					
	return  waw_dict
		
					
