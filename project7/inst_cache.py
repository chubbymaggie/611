#!/usr/bin/python
#THE INSTRUCTION CACHE IS FROM HEX 000 to HEX 100 byte addressed. 
#Which means there are that many bytes. IE from 0 to 255 bytes. 
#4 bytes make make one word. So there are 64 words in all that can be stored. 
#Each instruction is one word. The cache is 16 words. 4 words have to picked at a time. 

inst_cache = []
for i in range(0, 16):
	inst_cache.append([None, []])
print inst_cache

for i in range(0, 64):
	inst_cache[i % len(inst_cache)][1].append(i)
print inst_cache
#print [x[0] for x in inst_cache]			