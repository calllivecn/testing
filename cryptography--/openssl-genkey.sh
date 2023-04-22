#!/bin/bash
# date 2023-04-18 23:26:42
# author calllivecn <c-all@qq.com>

#openssl genpkey -algorithm X25519 -out private.pem -pkeyopt ec_paramgen_curve_name:X25519 -aes256

#openssl genpkey -algorithm X25519 -pkeyopt ec_paramgen_curve_name:X25519 -aes256

openssl genpkey -algorithm X25519 --outform DER
