#!/usr/bin/python3

from eth_account import Account
from web3.auto import w3
from eth_account.messages import encode_defunct



# generate account
print("generate account")
acct = Account.create()
address = acct.address
private_key = acct.key


# sign and verify message
print("sign message")
msg = "abcded"
message = encode_defunct(text=msg)
signed_message = w3.eth.account.sign_message(message, private_key=private_key)

print(signed_message)

print("verify signature")
recover_addr = w3.eth.account.recover_message(message, signature=signed_message.signature)
print(recover_addr)