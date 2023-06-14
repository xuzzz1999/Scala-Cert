from eth_account import Account
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct

import rsa
import random
import time
import copy
import math

import definition as df
import client as cl
import test_enclave

# (public_key, private_key) = rsa.newkeys(1024)  # 用于加密交易的公钥
# (public_key_sig, private_key_sig) = rsa.newkeys(1024)  # 用于远程认证签名
public_key, private_key = test_enclave.public_key, test_enclave.private_key
public_key_sig, private_key_sig = test_enclave.public_key_sig, test_enclave.private_key_sig


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


# step 2: 生成N笔交易，其中alpha个是机密的，beta1个是invalid的，即nonce或balance不对
def generate_transactions(N, accounts, account_states, alpha, beta1, level):
    txids = []
    txs = {}  # txid:tx
    for i in range(N):  # 前一半的账户作为sender
        sender = accounts[i]
        # 以beta1的概率产生大于balance的value，即invalid的交易
        if random.randint(0, 1000) < beta1 * 1000:
            value = account_states[sender.address].balance + 1
        else:
            balance = account_states[sender.address].balance
            value = random.randint(0, balance)
        data = "none"  # data置空
        recipient_addr = accounts[i + 1].address  # 后一半的账户作为recipient
        nonce = account_states[sender.address].nonce + 1  # nonce取正确的值
        # print(account_states[sender.address].nonce)
        tx = df.TX(value, data, recipient_addr, nonce)

        # 以alpha的概率设置交易为level保护级别

        if random.randint(0, 1000) < alpha * 1000:
            tx = cl.get_confidential_tx(level, public_key, tx, sender)
        else:
            tx.sig = cl.sign_tx_with_private_key(tx, sender.key).signature

        txid = cl.get_txid(tx)
        txs[txid] = tx
        txids.append(txid)

    return (txids, txs)


# leader,
def leader_ordering_validate(account_states, txids, txs, beta2):
    # start_time = time.time()

    # step 1: 验证sender公开的交易的签名和nonce
    verification_time = 0  # 验证的次数
    N = len(txids)
    temp_txs = copy.copy(txs)
    for txid, tx in temp_txs.items():
        if type(tx.nonce) == int:  # 利用nonce是否被加密判断sender是否公开
            # 若sender公开，验证签名是否正确
            verification_time += 1
            tx1 = copy.copy(tx)
            tx1.sig = "none"
            sender = cl.recover_addr_with_tx_and_signature(tx1, tx.sig)
            # 应该用try更合适，但是签名都是正确的，所以直接执行
            if tx.value > account_states[sender].balance:  # 如果余额不足，从交易列表删除该交易
                txid = cl.get_txid(tx)
                txids.remove(txid)
                del (txs[txid])
                continue
                # print('delete tx: ',txid)

    # step 2: ordering, 为便于计时，将三个step分开实现
    temp_txs = copy.copy(txs)  # 当前txs为去除不合法sender的交易列表
    ctxs = {}  # 用于记录机密交易
    non_ctxs = {}  # 用于记录非机密交易
    for txid, tx in temp_txs.items():
        if type(tx.nonce) != int or type(
                tx.data) != str:  # 利用nonce和data判断是否为confidential交易
            ctxs[txid] = tx
        else:
            non_ctxs[txid] = tx
    txs.clear()
    txs = {**ctxs, **non_ctxs}

    # step 3: pre_execution
    txs_copy = copy.copy(txs)
    for txid in txs_copy:
        for i in range(1000):
            i *= i
        # 以beta2的概率调用失败---补充：β已经代表了所有不合法交易的概率，无需额外增加recipient的失败
        if random.randint(0, 1000) < beta2 * 1000:
            txids.remove(txid)
            if txid in ctxs:
                del (ctxs[txid])
            else:
                del (non_ctxs[txid])

    # end_time = time.time()
    # print('runtime = ',(end_time-start_time))
    return (txids, txs, ctxs, verification_time)


def test_validate_time(account_states, txids, txs, beta2):

    origin_len = len(txids)

    runtime = 0

    start_time = time.time()
    (txids, txs, ctxs,
     verification_time) = leader_ordering_validate(account_states, txids, txs,
                                                   beta2)
    end_time = time.time()
    runtime = (end_time - start_time)

    aborted_transaction = origin_len - len(txids)

    # print('time of ordering. total runtime: ', round(runtime * 1000, 2),
    #       int(verification_time), int(aborted_transaction))

    return (ctxs, round(runtime * 1000,
                        2), int(verification_time), int(aborted_transaction))


def test_total(N, alpha, beta, level):
    beta1, beta2 = beta / 2, beta / 2
    (accounts, account_states) = generate_account(N)
    (txids, txs) = generate_transactions(N, accounts, account_states, alpha,
                                         beta1, level)

    # step 1: 测试leader
    (ctxs, leader_time, num_ver,
     num_abort) = test_validate_time(account_states, txids, txs, beta2)
    print('time_step1:', leader_time, 'num_ver:', num_ver, 'num_abort:',
          num_abort)

    # step 2: 调用enclave
    (er, time_total, time_sender, time_recipient,
     time_er) = test_enclave.enclave_execution(account_states, ctxs, beta2)
    # 返回时间以ms为单位
    print('time_step2:', time_total, 'time_sender:', time_sender,
          'time_recipient:', time_recipient, 'time_er:', time_er)


def main():

    # step 0: 生成交易和账户
    # N, alpha, beta, level = 300, 0.2, 0.2, 1
    # beta1, beta2 = beta / 2, beta / 2
    # for N in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]

    # 测试N的影响
    fr1 = open('f1_result', 'w')
    fr2 = open('f2_result', 'w')
    alpha, beta = 0.2, 0.2
    for level in [0, 1, 2]:
        for N in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]:
            # wstr = 'alpha=' + str(alpha) + ', beta=' + str(
            #     beta) + ', level=' + str(level) + ', N=' + str(N) + '\n'
            # fr.write(wstr)

            # 运行k次，以消除随机性带来的影响
            k = 1
            leader_times, num_vers, num_aborts = [], [], []
            time_totals, time_senders, time_recipients, time_ers = [],[],[],[]
            for i in range(k):
                # step 0: 生成账户和交易
                beta1, beta2 = beta / 2, beta / 2
                (accounts, account_states) = generate_account(N)
                (txids, txs) = generate_transactions(N, accounts,
                                                     account_states, alpha,
                                                     beta1, level)
                # step 1: 测试leader
                (ctxs, leader_time, num_ver,
                 num_abort) = test_validate_time(account_states, txids, txs,
                                                 beta2)
                leader_times.append(leader_time)
                num_vers.append(num_ver)
                num_aborts.append(num_abort)
                # step 2: 调用enclave
                (er, time_total, time_sender, time_recipient,
                 time_er) = test_enclave.enclave_execution(
                     account_states, ctxs, beta2)
                time_totals.append(time_total)
                time_senders.append(time_sender)
                time_recipients.append(time_recipient)
                time_ers.append(time_er)

            leader_time = sum(leader_times) / len(leader_times)
            num_ver = sum(num_vers) / len(num_vers)
            num_abort = sum(num_aborts) / len(num_aborts)
            time_total = sum(time_totals) / len(time_totals)
            time_sender = sum(time_senders) / len(time_senders)
            time_recipient = sum(time_recipients) / len(time_recipients)
            time_er = sum(time_ers) / len(time_ers)

            wstr = str(leader_time) + ' ' + str(num_ver) + ' ' + str(
                num_abort) + '\n'
            fr1.write(wstr)
            wstr = str(time_total) + ' ' + str(time_sender) + ' ' + str(
                time_recipient) + ' ' + str(time_er) + '\n'
            fr2.write(wstr)

            # # step 0: 生成账户和交易
            # beta1, beta2 = beta / 2, beta / 2
            # (accounts, account_states) = generate_account(N)
            # (txids, txs) = generate_transactions(N, accounts, account_states,
            #                                      alpha, beta1, level)

            # # step 1: 测试leader
            # (ctxs, leader_time, num_ver,
            #  num_abort) = test_validate_time(account_states, txids, txs, beta2)
            # # wstr = 'time_step1:' + str(leader_time) + ', num_ver:' + str(
            # #     num_ver) + ', num_abort:' + str(num_abort) + '\n'
            # wstr = str(leader_time) + ' ' + str(num_ver) + ' ' + str(
            #     num_abort) + '\n'
            # fr1.write(wstr)

            # # step 2: 调用enclave
            # (er, time_total, time_sender, time_recipient,
            #  time_er) = test_enclave.enclave_execution(account_states, ctxs,
            #                                            beta2)
            # # 返回时间以ms为单位
            # # wstr = 'time_step2:' + str(time_total) + ', time_sender:' + str(
            # #     time_sender) + ', time_recipient:' + str(
            # #         time_recipient) + ', time_er:' + str(time_er) + '\n'
            # wstr = str(time_total) + ' ' + str(time_sender) + ' ' + str(
            #     time_recipient) + ' ' + str(time_er) + '\n'
            # fr2.write(wstr)


if __name__ == '__main__':
    main()