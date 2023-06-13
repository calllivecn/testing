#!/bin/bash
# date 2023-06-13 19:52:22
# author calllivecn <c-all@qq.com>

TMP_CONF=$(mktemp -p /tmp/)
chmod 0600 "$TMP_CONF"

SECRETS_FILE="$HOME/.config/rsync/rsync_passwd"
SECRETS_FILE="rsyncd.secrets"
# 密码文件格式
# username:password\n

safe_exit(){
	rm -f $TMP_CONF
}

trap safe_exit ERR SIGTERM EXIT

cat > "$TMP_CONF" <<EOF
port = 1873
use chroot = no

auth users = rsync_backup
secrets file = $SECRETS_FILE

[mc18]
path = /mnt/data1/mc18
comment = MC 1.18.x directory

EOF

rsync -v --daemon --no-detach --config "$TMP_CONF"

