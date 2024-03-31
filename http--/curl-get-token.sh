#!/bin/bash
# date 2020-04-26 17:29:23
# author calllivecn <calllivecn@outlook.com>

# 需要在header中加入：X-Auth-Token

set -e

get_token(){
	local AUTH_ADDR="http://localhost:6789"
	local AUTH_ADDR="http://192.168.11.232:11000/sys/oapi/v1/double_factor/login"
	curl -k "$AUTH_ADDR" \
	-H "content-type: application/json" \
	-d '{
		"username":"admin",
		"password":"Y2xvdWRvcw==",
		"domain":"default",
		"userId":""	
	}' |jsonfmt.py --dot res.token
}

session(){
	local token token_file
	token_file="$HOME/.cache/session.token"

	if [ -f "$token_file" ];then
		:
	else
		token=$(get_token)
		echo "$now_time" > "$token_file"
		echo "$token" >> "$token_file"
	fi

	now_time=$(date +%s)
	save_time=$(sed -n '1p' "$token_file")
	internal=$[now_time - save_time]

	if [ $internal -ge 600 ];then

		token=$(get_token)
		echo "$now_time" > "$token_file"
		echo "$token" >> "$token_file"
		echo "$token"

	else
		token=$(sed -n '2p' "$token_file")
		echo "$token"
	fi
}

