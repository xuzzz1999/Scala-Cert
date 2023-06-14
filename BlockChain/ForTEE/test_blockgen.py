from eth_account import Account
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct

import rsa
import random
import time
import copy
import math
import json

import definition as df
import client as cl
import test_enclave
import test_ordering

# (public_key, private_key) = rsa.newkeys(1024)  # 用于加密交易的公钥
# (public_key_sig, private_key_sig) = rsa.newkeys(1024)  # 用于远程认证签名
public_key, private_key = test_enclave.public_key, test_enclave.private_key
public_key_sig, private_key_sig = test_enclave.public_key_sig, test_enclave.private_key_sig


def block_gen(ers, txs, account_states):
    print('test er:', ers[0])
    # step 1: verify each er in ers
    er0 = ers[0]
    for er in ers:
        # 1) verify remote attestation，为便于处理，所有签名都是正确的，没有错误处理
        # 验证签名
        if er == er0:
            er_tmp = copy.copy(er)
            ra = "none"  # 签名前将ra设置为none
            er_tmp["ra"] = ra
            er_tmp_jsonstr = json.dumps(er_tmp)
            rsa_verify = rsa.verify(er_tmp_jsonstr.encode(encoding='UTF-8'),
                                    er["ra"], public_key_sig)
            # print('rsa_verify: ', rsa_verify)

    # step 2: update account states and world state
    # 根据er0结果，修改tx
    # 1) 删除非法txid，并回滚对应的account state
    for txid in er["invalid_txids"]:
        tx = txs[txid]

        if type(tx.recipient) == str:  # recipient被预执行
            # 回滚recipient状态
            pass
        # 如何判断sender是否被预执行？ -- nonce
        if type(tx.nonce) == int:
            # 回滚sender状态
            pass

        del (txs[txid])  # 从交易列表删除

    # 2) update world state, ignore

    # step 3: generate and sign the block
    current_block = df.Block()
    print('test block:', current_block)

    # step 4: other T-verifiers validate and sign the block

    # step 5: organize final block


def test_blockgen():
    # step 0: 生成账户和交易
    N, alpha, beta, level = 50, 0.2, 0.2, 0
    beta1, beta2 = beta / 2, beta / 2
    (accounts, account_states) = test_ordering.generate_account(N)
    (txids, txs) = test_ordering.generate_transactions(N, accounts,
                                                       account_states, alpha,
                                                       beta1, level)
    # step 1: leader ordering
    (txids, txs, ctxs,
     __) = test_ordering.leader_ordering_validate(account_states, txids, txs,
                                                  beta2)

    # step 2: 调用enclave，生成m个er。为方便实现，直接复制er；不计入时间，无影响
    m = 10
    ers = []  # 每个er是一个字典对象
    (er, _, _, _, _) = test_enclave.enclave_execution(account_states, ctxs,
                                                      beta2)
    ers = [er for i in range(m)]

    # step 3: 将ers、txs送入block_gen，产生一个合法区块
    # 需要记录的就是这段时间
    block_gen(ers, txs, account_states)
    
    
    # step 4：验证block_gen生成的区块的合法性，对应validator的attestation步骤


def main():
    test_blockgen()


if __name__ == '__main__':
    main()