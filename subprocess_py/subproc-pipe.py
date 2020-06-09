#!/usr/bin/env python3
# coding=utf-8
# date 2020-06-09 17:12:39
# author calllivecn <c-all@qq.com>


from subprocess import run, PIPE


genkey = run('wg genkey'.split(), stdout=PIPE, text=True)

print("private key:", genkey.stdout)

pubkey = run('wg pubkey'.split(), input=genkey.stdout, stdout=PIPE, text=True)

print("public key:", pubkey.stdout)
