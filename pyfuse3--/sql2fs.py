#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-20 07:51:47
# author calllivecn <calllivecn@outlook.com>


import sqlite3
from pathlib import Path


class FS2DB:

    def __init__(self):
        pass


class Sql2fs:

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.sqlfile = self.root_path / Path("fsindex.db")
        self.data_root = self.root_path / Path("data")

        if self.sqlfile.exists():
            self.db_conn = sqlite3.connect(self.sqlfile)

    def 