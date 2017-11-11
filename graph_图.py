#!/usr/bin/env python3
#coding=utf-8


graph = {}
graph["you"] = ["alice", "bob", "claire"]
graph["bob"] = ["anuj", "peggy"]
graph["alice"] = ["peggy"]
graph["claire"] = ["thom", "jonny"]
graph["anuj"] = []
graph["peggy"] = []
graph["thom"] = []
graph["jonny"] = []



from queue import Queue

search_q = Queue()


search_q.put(graph.get("you"))

def person_is_seller(person):
    if person == "jonny":
        return True
    else:
        return False

while not search_q.empty():
    person = search_q.get()
    for name in person:
        if person_is_seller(name):
            print('找到了:',name)
        else:
            search_q.put(graph.get(name))



