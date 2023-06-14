from eth_account import Account
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct

import rsa
import random
import time
import copy
import hashlib
import json

import definition as df
import client as cl

(public_key, private_key) = rsa.newkeys(1024)  # 用于加密交易的公钥
(public_key_sig, private_key_sig) = rsa.newkeys(1024)  # 用于远程认证签名


# step 1: 创建2N个账户，为其初始化账户状态
def generate_account(N):
    accounts = []  # 存储账户
    account_states = {}  # 账户地址作为索引
    for i in range(2 * N):
        acct = Account.create()
        accounts.append(acct)
        state = df.Account_state()
        state.nonce = random.randint(0, 10)  # 设置nonce在0~10之间
        state.balance = random.randint(0, 50)  # 设置balance在0~50之间
        account_states[acct.address] = state
    return (accounts, account_states)


# step 2: 生成N笔交易，其中alpha个是机密的，beta个是invalid的，即nonce或balance不对
def generate_c_transactions(N, accounts, account_states, alpha, beta, level):
    txids = []
    ctxs = {}  # txid:tx，仅保存机密交易
    for i in range(N):  # 前一半的账户作为sender
        sender = accounts[i]
        # 以beta的概率产生大于balance的value，即invalid的交易

        if random.randint(0, 1000) < beta * 1000:
            value = account_states[sender.address].balance + 1
        else:
            balance = account_states[sender.address].balance
            value = random.randint(0, balance)  # 为了实现方便，规定value是int类型
        data = "none"  # data置空
        recipient_addr = accounts[i + 1].address  # 后一半的账户作为recipient
        nonce = account_states[sender.address].nonce + 1  # nonce取正确的值
        # print(account_states[sender.address].nonce)
        tx = df.TX(value, data, recipient_addr, nonce)

        # 以alpha的概率设置交易为level保护级别

        if random.randint(0, 1000) < alpha * 1000:
            tx = cl.get_confidential_tx(level, public_key, tx, sender)
            txid = cl.get_txid(tx)
            ctxs[txid] = tx
            txids.append(txid)
    #         print(
    #             'print protected txs, for verifying decryption correctness --- tx:',
    #             txid, 'sender:', sender.address, 'nonce:', nonce, 'recipient:',
    #             recipient_addr, 'data:', data, 'value: ', value)
    # print('test: number of protected tx:', len(ctxs))
    return (txids, ctxs)


# leader, step 1: 验证sender公开的交易的签名和nonce
def enclave_execution(account_states, ctxs, beta2):
    time_total_start = time.time()
    invalid_txids = []
    time_sender, time_recipient, time_er = 0, 0, 0

    temp_ctxs = copy.copy(ctxs)  # 复制ctxs用于遍历；非法交易直接从ctxs中删除
    for txid, tx in temp_ctxs.items():
        # step 1. 验证sender
        s_time = time.time()
        if type(tx.nonce) != int:  # 利用nonce是否被加密判断sender是否公开
            # 若sender机密，解密nonce并验证签名是否正确
            nonce_dec = rsa.decrypt(tx.nonce, private_key)  # 解密nonce，得到bytes结果
            nonce_str = str(nonce_dec)  # bytes转str
            nonce_str = nonce_str[2:-1]  # 去除 b' ' 标识符
            nonce = int(nonce_str)  # 转回int类型

            # 对conf.both和conf.sender需要分别处理
            if type(tx.value) == int:  # 利用value判断是否仅sender，value未加密说明仅sender
                tx1 = copy.copy(tx)
                tx1.nonce = nonce  # 写回 nonce
                tx1.sig = "none"  # 写回空签名
                sender = cl.recover_addr_with_tx_and_signature(
                    tx1, tx.sig)  # 恢复sender
                value = tx.value
                # print('test recover signature for conf.sender: txid:', txid,
                #       'sender:', sender)  # 验证成功
            else:  # 否则是全部加密，需要全部解密后再恢复签名
                # 解密value
                value_dec = rsa.decrypt(tx.value,
                                        private_key)  # 解密value，得到bytes结果
                value_str = str(value_dec)  # bytes转str
                value_str = value_str[2:-1]  # 去除 b' ' 标识符
                value = int(value_str)  # 转回int类型
                # print('test decrypt correctness of value:', value) # 验证成功
                # 解密recipient, 0x开头的以太坊地址、str类型
                recipient_dec = rsa.decrypt(tx.recipient, private_key)
                recipient_str = str(recipient_dec)
                recipient = recipient_str[2:-1]
                # print('test decrypt correctness of recipient:', recipient) # 验证成功
                # 解密data
                data_dec = rsa.decrypt(tx.data, private_key)
                data_str = str(data_dec)
                data = data_str[2:-1]
                # print('test decryt correctness of data:', data) # 验证成功

                tx1 = copy.copy(tx)
                tx1.value = value  # 写回value
                tx1.nonce = nonce  # 写回 nonce
                tx1.data = data
                tx1.recipient = recipient
                tx1.sig = "none"  # 写回空签名
                sender = cl.recover_addr_with_tx_and_signature(
                    tx1, tx.sig)  # 恢复sender
                # print('test for verification of conf.both, txid:', txid,
                #       'recover sender:', sender, 'with value: ',
                #       value)  # 验证成功，可以恢复出正确的sender地址

            # 根据机密状态验证sender余额
            balance = account_states[sender].balance
            if value > balance:  # 如果余额不足，将tx加入非法交易列表，并从ctx中将其删除
                invalid_txids.append(txid)
                del (ctxs[txid])
                # print('test invalid tx, invalid tx of sender: ', txid,
                #       'value is ', value, 'balance is ', balance)
                continue  # 若sender验证失败，无需执行recipient，直接跳到下一个交易
            # 至此完成对sender的验证
        e_time = time.time()
        time_sender += e_time - s_time

        # step 2. 执行recipient，对于conf.recipient和conf.both两类
        s_time = time.time()
        if type(tx.data) != str:  # 利用data是否被加密判断recipient是否公开
            # 若公开，则无需处理，因为leader在pre-execution已完成这部分调用
            # 若非公开，解密data，执行调用，更改其账户状态
            # 解密data
            data_dec = rsa.decrypt(tx.data, private_key)
            data_str = str(data_dec)
            data = data_str[2:-1]

            # 需要执行合约和更新状态，暂时用一段循环程序替代
            for i in range(1000):
                i *= i

            # print('execution of recipient')
            # 以beta2的概率调用失败---补充：β已经代表了所有不合法交易的概率，无需额外增加recipient的失败

            if random.randint(0, 1000) < beta2 * 1000:
                invalid_txids.append(txid)
                del (ctxs[txid])
                # print('test invalid tx, invalid tx of recipient: ', txid,
                #       'value is ', value, 'balance is ', balance)
        e_time = time.time()
        time_recipient += e_time - s_time

    # step 3. 生成 er=<txid_hex, invalid_txids, csr, eo, ra>

    s_time = time.time()
    er = {
        "txid_hex": "",
        "invalid_txids": "",
        "csr_old": "",
        "csr_new": "",
        "ra": ""
    }
    # 生成 txid_hex
    txid_str = ""
    for txid in ctxs:
        txid_str += str(txid)
    s = hashlib.sha256()
    s.update(txid_str.encode(encoding='UTF-8'))
    txid_hex = s.hexdigest()  # 生成保留的合法txid的hex
    er["txid_hex"] = txid_hex
    # 生成 invalid_txids
    er["invalid_txids"] = invalid_txids
    # 生成csr_old
    csr_old = "confidential_state_root_old"
    er["csr_old"] = csr_old
    # 生成csr_new
    csr_new = "confidential_state_root_new"
    er["csr_new"] = csr_new
    # 生成ra，使用私钥对json格式er签名
    ra = "none"  # 签名前将ra设置为none
    er["ra"] = ra
    er_jsonstr = json.dumps(er)

    # print('test er_str: ', er_jsonstr, 'type:', type(er_jsonstr))
    # 对er_jsonstr签名，使用SHA-1哈希
    er_sig = rsa.sign(er_jsonstr.encode(encoding='UTF-8'), private_key_sig,
                      'SHA-1')
    # print('test er signature: ', er_sig, 'type:', type(er_sig))
    ra = er_sig
    er["ra"] = ra
    e_time = time.time()
    time_er = e_time - s_time

    # 验证签名
    # rsa_verify = rsa.verify(er_jsonstr.encode(encoding='UTF-8'), er_sig,
    #                         public_key_sig)
    # print('rsa_verify: ', rsa_verify)
    time_total_end = time.time()

    return (er, round((time_total_end - time_total_start) * 1000,
                      2), round(time_sender * 1000,
                                2), round(time_recipient * 1000,
                                          2), round(time_er * 1000, 2))


def test_enclave_time_test():
    # 50, 100, 150, 200, 250, 300, 350, 400, 450, 500
    for N in [50, 250, 500]:
        # 生成账户
        (accounts, account_states) = generate_account(2 * N)
        alpha, beta1, beta2, level = 0.2, 0.1, 0.1, 2
        # 生成交易，导出机密交易列表
        txids, ctxs = generate_c_transactions(N, accounts, account_states,
                                              alpha, beta1, level)

        # enclave_execution
        # 多次运行消除随机性产生的影响

        k, run_time = 1, 0
        time_sender, time_recipient, time_er = 0, 0, 0
        for i in range(k):
            start_time = time.time()
            (er, time_sender_tmp, time_recipient_tmp,
             time_er_tmp) = enclave_execution(account_states, txids, ctxs,
                                              beta2)
            end_time = time.time()
            run_time += (end_time - start_time)
            time_sender += time_sender_tmp
            time_recipient += time_recipient_tmp
            time_er += time_er_tmp

        run_time /= k
        run_time = round(run_time * 1000, 2)  # 以毫秒为单位输出
        time_sender /= k
        time_sender = round(time_sender * 1000, 2)
        time_recipient /= k
        time_recipient = round(time_recipient * 1000, 2)
        time_er /= k
        time_er = round(time_er * 1000, 2)
        print("N=", N, "run_time:", run_time, "time_sender:", time_sender,
              "time_recipient:", time_recipient, "time_er:", time_er)

    # one time test
    # N = 50
    # (accounts, account_states) = generate_account(2 * N)
    # alpha, beta, level = 0.2, 0.2, 1
    # txids, ctxs = generate_c_transactions(N, accounts, account_states, alpha,
    #                                       beta, level)
    # er = enclave_execution(account_states, txids, ctxs)


def main():
    test_enclave_time()


if __name__ == '__main__':
    main()