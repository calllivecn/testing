#!/usr/bin/env python3
# coding=utf-8

import curses

try:
    cui = curses.initscr()

    H, W = cui.getmaxyx()

    print('H: {}\tW: {}'.format(H, W))

except Exception as e:
    print(e)

curses.endwin()
