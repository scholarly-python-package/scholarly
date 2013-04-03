#!/usr/bin/python

import sys
from scholar import searchAuthor
import json

center=searchAuthor(sys.argv[1]).next()
center.fillIn()

authors=set()
for p in center.publications:
    authors.update(p.authors)

authors=list(authors)
nodes=[ dict({'name':i,"type":"people"}) for i in authors]
pos=len(authors)
links=[]

for p in center.publications:
    #{"name":"Towards a Taint Mode for Cloud Computing Web Applications","type":"pub","cited":2}
    nodes.append({'name':p.title,'type':'pub','cited':p.citedBy})
    for i in p.authors:
        #{"source":1,  "target":0}
        links.append({'source':authors.index(i),'target':pos})
    pos+=1

f = open('collaborationMap/coauthorship.json', 'w')
f.write(json.dumps({'nodes':nodes,'links':links}))
f.close()
