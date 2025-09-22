
import json
import nftables

nft = nftables.Nftables()            # libnftables python binding
nft.set_json_output(True)            # 输出 JSON
nft.set_echo_output(True)            # 打开 echo（commit 后回显变更）
nft.set_handle_output(True)          # 输出 handle 字段

# 举例：在 inet family 的 mytable/mychain 加一条带 comment 的规则（帮助识别）
cmd = 'add rule inet filter input ip saddr 203.0.113.5 counter accept comment "marker:自定义标记"'
rc, out, err = nft.cmd(cmd)

if rc != 0:
    raise RuntimeError(f"nft failed: rc={rc}, err={err!r}")

# out 是 JSON 字符串，解析并查找 add->rule 的 handle
j = json.loads(out)
handle = None
for entry in j.get("nftables", []):
    add = entry.get("add")
    if add and "rule" in add:
        rule = add["rule"]
        # kernel-assigned handle 位于 rule['handle']
        handle = rule.get("handle")
        # 如果你同时添加多条规则，可能会有多次 add；按需要筛选
        break

print("new rule handle:", handle)

