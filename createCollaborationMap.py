#!/usr/bin/python

import sys
from scholar import searchAuthor
import json

center=searchAuthor(sys.argv[1]).next()
center.fillIn()

m=max([i.citedBy for i in center.publications[:15]])

if m > 10:
    m = 10/float(m)
else: m=1

authors=set()
for p in center.publications[:15]:
    authors.update(p.authors)

authors=list(authors)
nodes=[ dict({'name':i,"type":"people"}) for i in authors]
pos=len(authors)
links=[]

for p in center.publications[:15]:
    #{"name":"Towards a Taint Mode for Cloud Computing Web Applications","type":"pub","cited":2}
    nodes.append({'name':p.title,'type':'pub','cited':p.citedBy*m})
    for i in p.authors:
        #{"source":1,  "target":0}
        links.append({'source':authors.index(i),'target':pos})
    pos+=1

f = open('collaborationMap/coauthorship.json', 'w')
f.write(json.dumps({'nodes':nodes,'links':links}))
f.close()
