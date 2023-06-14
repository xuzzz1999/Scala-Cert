#!/usr/bin/python3

from web3 import Web3
from eth_account import Account
from web3.auto import w3
from eth_account.messages import encode_defunct

import rsa
import copy

# GAS_LIMIT_BLOCK = 100000000
# GAS_LIMIT_TRANSACTION = 100000000
# GAS_FEE = 50


class TX:

    def __init__(self, value, data, recipient, nonce):
        self.value = value
        self.data = data
        self.recipient = recipient
        self.nonce = nonce
        self.sig = "none"
        self.gasLimit = 0  # 实现中忽略了gas的处理，全部置零
        self.maxPriorityFeePerGas = 0
        self.maxFeePerGas = 0

    def to_string(self):  # 转str，在签名前使用
        tx_str = str(self.value) + str(self.data) + str(self.recipient) + str(
            self.nonce) + str(self.gasLimit) + str(
                self.maxPriorityFeePerGas) + str(self.maxFeePerGas)
        return (tx_str)

    def to_string_print(self):  # 打印查看交易信息
        tx_str = str(self.value) + '\n' + str(self.data) + '\n' + str(
            self.recipient) + '\n' + str(self.nonce) + '\n' + str(
                self.sig) + '\n' + str(self.gasLimit) + '\n' + str(
                    self.maxPriorityFeePerGas) + '\n' + str(self.maxFeePerGas)
        return (tx_str)

    def to_bytes(self):
        tx_str = str(self.value) + self.data + self.recipient + str(
            self.nonce) + str(self.gasLimit) + str(
                self.maxPriorityFeePerGas) + str(self.maxFeePerGas)
        tx_bytes = Web3.toBytes(text=tx_str)
        return (tx_bytes)


class Execution_payload_header:

    def __init__(self):
        self.parent_hash = "parent_hash"
        self.fee_recipient = "fee_recipient"
        self.state_root = "state_root"
        self.receipts_root = "receipts_root"
        self.logs_bloom = "logs_bloom"
        self.prev_randao = "prev_randao"
        self.block_number = "block_number"
        self.gas_limit = "gas_limit"
        self.gas_used = "gas_used"
        self.timestamp = "timestamp"
        self.extra_data = "extra_data"
        self.base_fee_per_gas = "base_fee_per_gas"
        self.block_hash = "block_hash"
        self.transactions_root = "transactions_root"

    # def __init__(self, parent_hash, fee_recipient, state_root, receipts_root,
    #              logs_bloom, prev_randao, block_number, gas_limit, gas_used,
    #              timestamp, extra_data, base_fee_per_gas, block_hash,
    #              transactions_root):
    #     self.parent_hash = parent_hash
    #     self.fee_recipient = fee_recipient
    #     self.state_root = state_root
    #     self.receipts_root = receipts_root
    #     self.logs_bloom = logs_bloom
    #     self.prev_randao = prev_randao
    #     self.block_number = block_number
    #     self.gas_limit = gas_limit
    #     self.gas_used = gas_used
    #     self.timestamp = timestamp
    #     self.extra_data = extra_data
    #     self.base_fee_per_gas = base_fee_per_gas
    #     self.block_hash = block_hash
    #     self.transactions_root = transactions_root


class Execution_payload:

    def __init__(self):
        self.parent_hash = "parent_hash"
        self.fee_recipient = "fee_recipient"
        self.state_root = "state_root"
        self.receipts_root = "receipts_root"
        self.logs_bloom = "logs_bloom"
        self.prev_randao = "prev_randao"
        self.block_number = "block_number"
        self.gas_limit = "gas_limit"
        self.gas_used = "gas_used"
        self.timestamp = "timestamp"
        self.extra_data = "extra_data"
        self.base_fee_per_gas = "base_fee_per_gas"
        self.block_hash = "block_hash"
        self.transactions = "transactions"

    # def __init__(self, parent_hash, fee_recipient, state_root, receipts_root,
    #              logs_bloom, prev_randao, block_number, gas_limit, gas_used,
    #              timestamp, extra_data, base_fee_per_gas, block_hash,
    #              transactions):
    #     self.parent_hash = parent_hash
    #     self.fee_recipient = fee_recipient
    #     self.state_root = state_root
    #     self.receipts_root = receipts_root
    #     self.logs_bloom = logs_bloom
    #     self.prev_randao = prev_randao
    #     self.block_number = block_number
    #     self.gas_limit = gas_limit
    #     self.gas_used = gas_used
    #     self.timestamp = timestamp
    #     self.extra_data = extra_data
    #     self.base_fee_per_gas = base_fee_per_gas
    #     self.block_hash = block_hash
    #     self.transactions = transactions


class Attestations:

    def __init__(self):
        self.aggregation_bits = "aggregation_bits"
        self.slot = "slot"
        self.index = "index"
        self.beacon_block_root = "beacon_block_root"
        self.source = "source"
        self.target = "target"
        self.signature = "signature"

    # def __init__(self, aggregation_bits, slot, index, beacon_block_root,
    #              source, target, signature):
    #     self.aggregation_bits = aggregation_bits
    #     self.slot = slot
    #     self.index = index
    #     self.beacon_block_root = beacon_block_root
    #     self.source = source
    #     self.target = target
    #     self.signature = signature


class Block_body:

    def __init__(self):
        self.randao_reveal = "randao_reveal"
        self.eth1_data = "eth1_data"
        self.graffiti = "graffiti"
        self.proposer_slashings = "proposer_slashings"
        self.attester_slashings = "attester_slashings"
        self.attestations = "attestations"
        self.deposits = "deposits"
        self.voluntary_exits = "voluntary_exits"
        self.sync_aggregate = "sync_aggregate"
        self.execution_payload = "execution_payload"

    # def __init__(self, randao_reveal, eth1_data, graffiti, proposer_slashings,
    #              attester_slashings, attestations, deposits, voluntary_exits,
    #              sync_aggregate, execution_payload):
    #     self.randao_reveal = randao_reveal
    #     self.eth1_data = eth1_data
    #     self.graffiti = graffiti
    #     self.proposer_slashings = proposer_slashings
    #     self.attester_slashings = attester_slashings
    #     self.attestations = attestations
    #     self.deposits = deposits
    #     self.voluntary_exits = voluntary_exits
    #     self.sync_aggregate = sync_aggregate
    #     self.execution_payload = execution_payload


class Block:

    def __init__(self):
        self.slot = "slot"
        self.proposer_index = "proposer_index"
        self.parent_root = "parent_root"
        self.state_root = "state_root"
        self.body = "body"  # a Block_body object

    # def __init__(self, slot, proposer_index, parent_root, state_root, body):
    #     self.slot = slot
    #     self.proposer_index = proposer_index
    #     self.parent_root = parent_root
    #     self.state_root = state_root
    #     self.body = body  # a Block_body object


class Account_state:

    def __init__(self) -> None:
        self.nonce = 0
        self.balance = 0
        self.codeHash = ""
        self.storageRoot = ""


def generateTx(n, alpha):  # 生成当前slot的交易集，共n个交易，其中α为机密交易
    pass


def main():
    tx = TX()
    tx.value = 1
    print(tx.value)


if __name__ == '__main__':
    main()
