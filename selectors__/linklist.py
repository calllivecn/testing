#!/usr/bin/env python3
# coding=utf-8
# date 2021-05-13 21:38:26
# author calllivecn <calllivecn@outlook.com>

import time

class SockMon:
    """
    sock(一个socket)，和 time.montonic组成的数据结构
    """
    __slots__ = ("sock", "monotonic", "pre", "pnext")

    def __init__(self, sock, monotonic):
        self.sock = sock
        self.monotonic = monotonic
        self.pre = None
        self.pnext = None
    
    def __str__(self):
        return f"{str(self.sock)}:{self.monotonic} --> "


class Linklist:
    """
    单向链表
    """

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
        print()

class DuLinklist:
    """
    双向链表
    """

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
        # 这里只需要从头插数据
        if self.head is None:
            self.head = sockmon
            self.tail = sockmon

        else:
            sockmon.pnext = self.head
            self.head = sockmon
        
        self.length += 1


    def head_delete(self):
        now = time.monotoinc()
        pre_now = now - 45

        # 超时了的socket
        socks = []

        if self.head == None:
            return socks
        
        while self.head != None:

            if self.head.monotonic > pre_now:
                socks.append(self.head)

            self.head = self.head.pnext
        
        self.length -= 1

        return socks
    
    def append(self, sockmon):
        if self.tail is None:
            self.head = sockmon
            self.tail = sockmon
        else:
            self.tail.pnext = sockmon
            sockmon.pre = self.tail
            self.tail = sockmon
        
        self.length += 1

    def update(self, sockmon):
        """
        这是的 update (当前是测试); 把一个节点移到链尾。
        """

        # 如果这是第一个node。
        if sockmon == self.head:
            if sockmon.pnext != None:
                self.head = sockmon.pnext
                self.head.pre = None
                self.tail.pnext = sockmon
                sockmon.pre = self.tail
                self.tail = sockmon
                self.tail.pnext = None
            else:
                self.tail = self.head

        # 如果这是尾node, 不用做
        # elif sockmon == self.tail:
            # self.tail.pnext = None

        # 如果不是头，也不是尾；那至少有3个元素；sockmon.pre 和 sockmon.pnext 不为 None 。移动它
        elif sockmon != self.head and sockmon != self.tail:
            sockmon.pre.pnext = sockmon.pnext
            sockmon.pnext.pre = sockmon.pre
            sockmon.pre = self.tail
            self.tail.pnext = sockmon
            self.tail = sockmon
            self.tail.pnext = None


    def print(self):
        print("这是正输出：")
        cur = self.head
        while cur != None:
            print(cur, end="")
            cur = cur.pnext
        print()
                
    def pre_print(self):
        print("这是反输出：")
        tail = self.tail
        while tail != None:
            print(tail, end="")
            tail = tail.pre
        print()

print("="*40)
print("单向链表测试:")

ll = Linklist()

ll.append(SockMon("sock1", 1))

sockmon_new = SockMon("sock2", 2)
ll.append(sockmon_new)

ll.append(SockMon("sock3", 3))
ll.append(SockMon("sock4", 4))

ll.print()

sockmon_new.monotonic = 5

ll.update(sockmon_new)

ll.append(SockMon("sock8", 8))

ll.print()

print("="*40)
print("单向链表测试 done")


print("="*40)
print("双向链表测试:")

dul = DuLinklist()

dul.append(SockMon("sock1", time.monotonic()))
sockmon_new = SockMon("sock2", time.monotonic())
dul.append(sockmon_new)
dul.append(SockMon("sock3", time.monotonic()))
dul.append(SockMon("sock4", time.monotonic()))

dul.print()

sockmon_new.monotonic = time.monotonic()
dul.update(sockmon_new)

dul.print()

dul.pre_print()

print("="*40)
print("双向链表测试 done")

print("="*40)
print("双向链表测试 一个节点，并更新")

dul2 = DuLinklist()

update_node = SockMon("5", time.monotonic())
dul2.append(update_node)
dul2.append(SockMon("6", time.monotonic()))
dul2.append(SockMon("7", time.monotonic()))

print("更新前")
dul2.print()
dul2.update(update_node)
print("更新后")
dul2.print()
input()
dul2.pre_print()
print(f"debug length: {dul2.length}")