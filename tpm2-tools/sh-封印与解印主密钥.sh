#!/usr/bin/bash

set -e

CTX="tpm2_ctx"

mkdir -vp "$CTX"

trap "rm -rfv ${CTX}" EXIT


# ----------------------------------------------------
# 1. 生成基于 PCR 7 的 Policy 策略摘要
# ----------------------------------------------------
# 创建策略会话 (-s 指定输出会话上下文文件)
tpm2_startauthsession --policy-session -S "$CTX"/session.ctx

# 计算 PCR 7 哈希并导出策略摘要 (-S 传入会话，-L 导出摘要文件)
tpm2_policypcr -S "$CTX"/session.ctx -l sha256:7 -L "$CTX"/pcr7.policy

# 刷新并释放临时会话
tpm2_flushcontext "$CTX"/session.ctx

# ----------------------------------------------------
# 2. 生成测试主密钥并进行封包 (Seal)
# ----------------------------------------------------
# 生成 32 字节随机主密钥
openssl rand -out "$CTX"/master.key 32

# 创建存储根密钥 (SRK)
tpm2_createprimary -C o -g sha256 -G rsa -c "$CTX"/primary.ctx

# 封包数据 (v5.7 下封包使用 -G keyedhash)
tpm2_create -C "$CTX"/primary.ctx -g sha256 \
  -p "MySecretPIN" \
  -L "$CTX"/pcr7.policy \
  -i "$CTX"/master.key \
  -u "$CTX"/key.pub \
  -r "$CTX"/key.priv

# 删除磁盘上的明文主密钥
#rm -f "$CTX"/master.key
sha256sum "$CTX"/master.key

# ----------------------------------------------------
# 3. 运行时加载与解封 (Unseal)
# ----------------------------------------------------
# 将封包好的密钥对象加载到 TPM
tpm2_load -C "$CTX"/primary.ctx -u "$CTX"/key.pub -r "$CTX"/key.priv -c "$CTX"/key.ctx

# 创建解封用的策略会话
tpm2_startauthsession --policy-session -S "$CTX"/session.ctx

# 灌入当前的 PCR 7 实时状态以匹配 Policy
tpm2_policypcr -S "$CTX"/session.ctx -l sha256:7

# 结合 Policy 会话与用户 PIN 执行解封
tpm2_unseal -c "$CTX"/key.ctx -p "session:${CTX}/session.ctx+MySecretPIN" -o "$CTX"/unsealed_master.key

tpm2_flushcontext "$CTX"/session.ctx
# 在 tpm2-tools 中，当你通过 -p session:... 或 -S 将 Policy Session 传入 tpm2_unseal 执行授权时，该 Session 属于一次性消耗品，命令执行完毕后 TPM 内部和 TSS 库会自动释放并销毁该 Session。

# 清理 TPM 中的临时会话与对象句柄
#tpm2_flushcontext "$CTX"/key.ctx


# 验证解封所得文件大小 (应为 32 字节)
ls -l "$CTX"/unsealed_master.key
sha256sum "$CTX"/unsealed_master.key
