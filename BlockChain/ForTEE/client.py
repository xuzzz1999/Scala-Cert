#!/usr/bin/python3

from eth_account import Account
from web3.auto import w3
from web3 import Web3
from eth_account.messages import encode_defunct

import rsa
import copy

import definition as df


def get_txid(tx):
    tx_str = tx.to_string()
    txid = Web3.keccak(text=tx_str)
    txid = Web3.toHex(txid)
    return (txid)  # 返回hex格式txid


# level: 0 for all protected, 1 for only protected sender, 2 for only protected recipient
# public_key is used to encryt protected contents, is a RSA public key
def generate_confidential_tx(level, public_key):
    sender = Account.create()
    recipient = Account.create()
    (public_key, private_key) = rsa.newkeys(1024)
    recipient_addr = recipient.address
    tx = df.TX(value=10, data="none-data", recipient=recipient_addr, nonce=0)

    # encrypt contents for different level
    if level == 0:  # all protected
        tx.sig = sign_tx_with_private_key(tx, sender.key).signature
        tx.value = rsa.encrypt(str(tx.value).encode('utf-8'), public_key)
        tx.data = rsa.encrypt(str(tx.data).encode('utf-8'), public_key)
        tx.recipient = rsa.encrypt(tx.recipient.encode('utf-8'), public_key)
        tx.nonce = rsa.encrypt(str(tx.nonce).encode('utf-8'), public_key)
    elif level == 1:
        tx.sig = sign_tx_with_private_key(tx, sender.key).signature
        tx.nonce = rsa.encrypt(str(tx.nonce).encode('utf-8'), public_key)
    elif level == 2:
        tx.data = rsa.encrypt(str(tx.data).encode('utf-8'), public_key)
        tx.recipient = rsa.encrypt(tx.recipient.encode('utf-8'), public_key)
        tx.sig = sign_tx_with_private_key(tx, sender.key).signature
    return (tx)


def get_confidential_tx(level, public_key, tx, sender):
    # encrypt contents for different level
    if level == 0:  # all protected
        tx.sig = sign_tx_with_private_key(tx, sender.key).signature
        tx.value = rsa.encrypt(str(tx.value).encode('utf-8'), public_key)
        tx.data = rsa.encrypt(str(tx.data).encode('utf-8'), public_key)
        tx.recipient = rsa.encrypt(tx.recipient.encode('utf-8'), public_key)
        tx.nonce = rsa.encrypt(str(tx.nonce).encode('utf-8'), public_key)
    elif level == 1:  # conf.sender
        tx.sig = sign_tx_with_private_key(tx, sender.key).signature
        tx.nonce = rsa.encrypt(str(tx.nonce).encode('utf-8'), public_key)
    elif level == 2:  # conf.recipient
        tx.data = rsa.encrypt(str(tx.data).encode('utf-8'), public_key)
        tx.recipient = rsa.encrypt(tx.recipient.encode('utf-8'), public_key)
        tx.sig = sign_tx_with_private_key(tx, sender.key).signature
    return (tx)


def sign_tx_with_private_key(tx, private_key):
    msg = tx.to_string()
    message = encode_defunct(text=msg)
    signed_message = w3.eth.account.sign_message(message,
                                                 private_key=private_key)
    return (signed_message)


def recover_addr_with_tx_and_signature(tx, signed_tx):
    msg = tx.to_string()
    message = encode_defunct(text=msg)
    recover_addr = w3.eth.account.recover_message(message, signature=signed_tx)
    return (recover_addr)


# following are test functions
def test_rsa():
    (public_key, private_key) = rsa.newkeys(1024)
    message = "test rsa".encode('utf-8')
    cipher_text = rsa.encrypt(message, public_key)
    print(cipher_text)
    decrypt = rsa.decrypt(cipher_text, private_key)
    print(decrypt)


def test_account_and_sign():
    sender = Account.create()  # create ethereum account
    private_key = sender.key  # get private key
    recipient = Account.create()
    recipient_address = recipient.address
    tx = df.TX(10, 'none-date', recipient_address, 0)
    print('generate a tx: ', tx.to_string())
    signed_tx = sign_tx_with_private_key(tx, private_key).signature
    print('signed_tx: ', signed_tx)
    tx.sig = signed_tx
    tx1 = copy.copy(tx)
    tx1.sig = "none"
    recover_addr = recover_addr_with_tx_and_signature(tx1, tx.sig)
    print('recover address: ', recover_addr)


def test_generate_confidential_tx():
    sender = Account.create()
    recipient = Account.create()
    (public_key, private_key) = rsa.newkeys(1024)
    recipient_addr = recipient.address
    print(recipient_addr, type(recipient_addr))

    # encrypted_recipient = rsa.encrypt(recipient_addr.encode('utf-8'),public_key)
    # print(encrypted_recipient)
    # decrypt = rsa.decrypt(encrypted_recipient, private_key)
    # print(decrypt)

    tx = df.TX(value=10, data="none-data", recipient=recipient_addr, nonce=0)
    tx.recipient = rsa.encrypt(tx.recipient.encode('utf-8'),
                               public_key)  # rsa.encrypt输出bytes格式密文
    print(tx.to_string_print())
    decrypt = rsa.decrypt(tx.recipient, private_key)
    print(decrypt)


# 创建公私钥、创建机密交易、对level-2验证签名、生成txid
def test_entire_transaction():
    (public_key, private_key) = rsa.newkeys(1024)
    level = 2
    tx = generate_confidential_tx(2, public_key)
    if level == 2:
        tx1 = copy.copy(tx)
        tx1.sig = "none"
        recover_addr = recover_addr_with_tx_and_signature(tx1, tx.sig)
        # print(recover_addr)
    txid = get_txid(tx)
    # print(txid)
    print(tx.nonce)


def main():
    test_entire_transaction()

    # step 1: client: generate n transactions, with alpha confidential, for all 0-level, all 1-level, all 2-level, mix-level

    # step 2: leader: ordering
    # 2.1 verify public part
    # 2.2 handle conflict
    # 2.3 generate confidential list, compute hash and sign, then broadcast


if __name__ == '__main__':
    main()
