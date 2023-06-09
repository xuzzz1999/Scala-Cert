###########################################################
# Package: BlockChain
# Filename: block
# Time: Apr 26, 2019 at 10:21:36 AM
############################################################

from enum import Enum
import time
import json
import os
import threading,socket
import random
from .mycrypto import *
from .block import Block
from .server import NodeServer
from .client import sender, broadcast, loadjson, dumpjson, isconse
from .certificate import *

class NodeAddr(dict):
    __doc__ = "network addr"

    def __init__(self, addr_dict):
        super(NodeAddr,self).__init__()
        self["ip"] = addr_dict["ip"]
        self["port"] = addr_dict["port"]

    def __eq__(self, other):
        return self["ip"] == other["ip"] and self["port"] == other["port"]


class ConsenseMethod(Enum):
    # 共识机制的编号 ... 可能只实现其中一个
    POW = 0
    PBFT = 1
    POS = 2

class Node(object):

    __doc__ = "This is a node in the block chain network"

    def __init__(self, name, config, consensus = ConsenseMethod.POW, diff=4):

        # Ip Config
        self.name = name
        self.addr = NodeAddr(config["addr"])    # Address
        self.peers = []                         # Other nodes in the network
        for peer in config['peers']:
            self.peers.append(NodeAddr(peer))
        self.isMain = config["role"] == 1    # Is Main Server

        if self.isMain :
            self.mainAddr = self.addr
        else:
            self.mainAddr = None

        # Public Key and Private Key
        self.priv_key_file = "keys/"+self.name+"_priv.cer"
        self.pub_key_file = "keys/"+self.name+"_pub.cer"
        self.priv_ckey_file = "keys/"+self.name+"_cpriv_cer"
        self.pub_ckey_file = "keys/"+self.name+"_cpub_cer"

        self.priv_key, self.pub_key = open_key(self.priv_key_file, self.pub_key_file)
        # chameleon key
        self.priv_ckey,self.pub_ckey = open_ckey(self.priv_ckey_file,self.pub_ckey_file)
        # Data Config
        self.blocks = []
        for block in config["block"]:
            nb = Block([])
            nb.init_from_json(json.dumps(block))
            self.blocks.append(nb)

        # Consensus Config
        self.consensus = consensus
        self.status = False
        self.server = NodeServer(self,self.addr)

        # POW
        self.diff = diff
        if len(self.blocks) == 0:
            self.newblock = Block([], height=len(self.blocks), diff=self.diff,
                              timeStamp=None, prevBlockHash="")
        else:
            self.newblock = Block([], height=len(self.blocks), diff=self.diff,
                              timeStamp=None, prevBlockHash=self.blocks[-1].gethash())
        self.alock = threading.Lock()
        self.signal = dict() # 信号 用于事件驱动
        self.signal['needImport'] = True


    def print_block(self):
        for bl in self.blocks:
            print(bl)

    def run(self):
        #self.find_main()
        self.runserver()

        while True:
            while self.signal['needImport'] == True:
                self.signal['needImport'] = not self.request_block()
    
            self.import_blocks()
            result = self.newblock.pow(self.diff)
            if result:
                self.add_block()
                self.redact_blocks()
                with open("data/"+ self.name + ".txt","w") as f:
                    for bl in self.blocks:
                        f.writelines(bl.__str__() + "\n")
                time.sleep(random.random())

    def runserver(self):
        self.server.start()

    def find_main(self):
        if not self.mainAddr:
            rets = broadcast(self.peers,dumpjson("getinfo",""))
            for ret in rets:
                if ret != 'Error':
                    self.mainAddr = NodeAddr(ret['main'])
                    break
            print("Info: Change Main Address to {}".format(self.mainAddr))

    def set_main(self, addr):
        rets = broadcast(self.peers,dumpjson("setmain_pre",addr))
        count = 0
        success = 0

        for ret in rets:
            if ret != 'Error':
                count += 1
                if ret:
                    success += 1

        if isconse(success,count):
            broadcast(self.peers, dumpjson("setmain_after", True))
        else:
            broadcast(self.peers, dumpjson("setmain_after", False))
        self.mainAddr = addr
        print("Info: Change Main Address to {}".format(self.mainAddr))

    def testalive(self, addr=None):
        if not addr:
            addr = self.mainAddr
        ret = sender(self.mainAddr, dumpjson("isalive",""))
        return ret == True

    # Create a new block used in POW
    def add_block(self):
        self.server.store["cache_lock"].acquire()
        cache = self.server.store['cache'].copy()
        self.server.store['cache'] = []
        self.server.store["cache_lock"].release()

        self.alock.acquire()
        if self.newblock:

            self.newblock.sign.append(
                {
                    'signer': self.name,
                    'sign': sign( self.priv_key, json.dumps(self.newblock.sign_content()))
                }
            )
            print("create: " + str(self.newblock))
            self.blocks.append(self.newblock)
        self.newblock = Block([], height=len(self.blocks), diff=self.diff, timeStamp=None,
                              prevBlockHash=self.blocks[-1].gethash())
        self.newblock.append(cache)
        self.newblock.flesh(len(self.blocks),self.blocks[-1].gethash())
        self.alock.release()

        # SEND THE NEW BLOCK
        self.boardcast_block(self.blocks[-1])

    def import_blocks(self):
        if len(self.server.tmpBlock) == 0:
            return True
        self.server.tmpBlockLock.acquire()
        cache = self.server.tmpBlock.copy()
        self.server.tmpBlock = []
        self.server.tmpBlockLock.release()

        for js in cache:
            self.import_block(js)
        return True

    # Import a new block from network
    def import_block(self, js):
        self.alock.acquire()
        tmpBlock = Block([])
        ret = tmpBlock.init_from_json(js)
        if ret != -1:
            print("Data Broken.")
            self.signal['needImport'] = True
        elif tmpBlock.height > self.blocks[-1].height + 1:
            print("Warming: Need to Rebuild the chain")
            self.signal['needImport'] = True
        elif tmpBlock.height <= self.blocks[-1].height:
            print("Warming: Ingore block")
        elif tmpBlock.height != 0 and tmpBlock.prevBlockHash != self.blocks[-1].gethash():
            print("Warming: Hash is not corect")
            self.signal['needImport'] = True
        else:
            self.blocks.append(tmpBlock)
            self.newblock.flesh(len(self.blocks),self.blocks[-1].gethash())
        self.alock.release()

    def redact_blocks(self):
        newblock = self.blocks[-1]
        for da in newblock.data:
            if da['types'] != "Revoke":
                pass
            else:
                seri = da['serial']
                for cer in self.blocks[da['LastOperateHeight']].data:
                    if cer['serial'] == seri:
                        c = Certificate()
                        c.load_dict(cer)
                        c.modify_height(da['currentHeight'],self.priv_ckey)
                        cer['LastOperateHeight'] = da['currentHeight']
                        cer['nonce'] = c.nonce
                        print("redact: " + str(self.blocks[da['LastOperateHeight']]))
        return True

    def boardcast_block(self, bl):
        broadcast(self.peers, dumpjson("resv_block", bl.__str__()))

    # TBD
    def request_block(self):
        rets = broadcast(self.peers,dumpjson('request_block', ''))
        HighestRet = {'height': 0, 'data': []}

        for ret in rets:
            if ret == 'Error':
                continue
            elif ret['height'] > HighestRet['height']:
                HighestRet = ret

        if len(self.blocks) != 0 and HighestRet['height'] <= self.blocks[-1].height + 1:
            return True

        self.server.store["cache_lock"].acquire()
        self.server.store['cache'] = []
        self.server.store["cache_lock"].release()

        self.blocks = []
        for js in HighestRet['data']:
            tmpBlock = Block([])
            msg = tmpBlock.init_from_json(js)
            if msg != -1:
                print("Data Broken.")
                return False
            if tmpBlock.height != 0 and tmpBlock.prevBlockHash != self.blocks[-1].gethash():
                print("Error: Hash Error")
                return False
            else:
                self.alock.acquire()
                self.blocks.append(tmpBlock)
                self.newblock.flesh(len(self.blocks), self.blocks[-1].gethash())
                self.alock.release()
        self.print_block()
        return True


