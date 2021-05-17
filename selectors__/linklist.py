#!/usr/bin/env python3
# coding=utf-8
# date 2021-05-13 21:38:26
# author calllivecn <c-all@qq.com>

class SockMon:
    """
    sock(一个socket)，和 time.montonic组成的数据结构
    """
    __slots__ = ("sock", "montonic", "pnext")

    def __init__(self, sock, montonic):
        self.sock = sock
        self.montonic = montonic
        self.pnext = None
    
    def __str__(self):
        if self.pnext == None:
            return f"{str(self.sock)}:{self.montonic}\n"
        else:
            return f"{str(self.sock)}:{self.montonic} --> "


class Linklist:

    __slots__ = (
                "sockmon",
                "head",
                "tail",
                "length"
                )

    def __init__(self, head=None):
        self.head = head
        self.tail = self.head

        self.length = 0

    def insert(self, sockmon):
        if self.head is None:
            self.head = sockmon
            self.tail = sockmon

        else:
            sockmon.pnext = self.head
            self.head = sockmon
        
        self.length += 1


    def frist_delete(self):
        if self.head == None:
            return -1
        else:
            self.head = self.head.pnext
        
        self.length -= 1
    
    def append(self, sockmon):
        if self.tail is None:
            self.head = sockmon
            self.tail = sockmon
        else:
            self.tail.pnext = sockmon
            self.tail = sockmon
            self.tail.pnext = None
        
        self.length += 1

    def update(self, sockmon):
        cur = self.head
        pre = None

        # 当前是空链表
        # if cur is None:
            # return -1

        while cur != None:
            # 如果找到要更新的节点
            if cur.sock == sockmon.sock:
                # 当前第一个元素，更新
                if pre == None:
                    self.head = cur.pnext
                    self.tail.pnext = sockmon
                    self.tail = sockmon
                    self.tail.pnext = None
                else:
                    # 把前一个的 pnext 指向 cur 的下一个, 把 cur 从链表中间全
                    pre.pnext = cur.pnext
                    # 把 cur 放到尾巴，并 self.tail 指向 cur
                    self.tail.pnext = cur
                    self.tail = cur
                    # 把 self.tail.pnext 置空，表示是最后一个元素
                    self.tail.pnext = None
            
                break
            # 否则 继续
            else:
                if pre == None:
                    pre = cur
                else:
                    pre = cur
                    cur = cur.pnext


    def print(self):
        cur = self.head
        while cur != None:
            print(cur, end="")
            cur = cur.pnext
                


ll = Linklist()

ll.append(SockMon("sock1", 1))

sockmon_new = SockMon("sock2", 2)
ll.append(sockmon_new)

ll.append(SockMon("sock3", 3))
ll.append(SockMon("sock4", 4))

ll.frist_delete()

ll.print()

sockmon_new.montonic = 5

ll.update(sockmon_new)

ll.append(SockMon("sock8", 8))

ll.print()

