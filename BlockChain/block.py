###########################################################
# Package: BlockChain
# Filename: block
# Time: Apr 25, 2019 at 9:11:15 PM
############################################################

import time
import json

from BlockChain.certificate import Certificate
from . import mycrypto
import threading



class Block(object):
        __doc__ = '''This class define the structure of a block'''

        height = 0
        version = 1                             # Version Number
        prevBlockHash = ""                      # PrevBlockHash
        merkleTree = None                       # Merkle Tree
        timeStamp = 0                           # Time
        nonce = 0                               # Nonce
        data = []                               # Data
        sign = []                               # sign used in the PBFT

        def __init__(self, data, height = 0,diff = 5, timeStamp = None, prevBlockHash = ""):
            self.height = height
            self.version = 1
            self.nonce = 0
            self.sign = []
            self.diff = diff
            self.data = data
            self.prevBlockHash = prevBlockHash
            if not timeStamp:
                self.timeStamp = time.time()
            else:
                self.timeStamp = timeStamp
            self.merkleTree = MerkleTree(self.data)
            # self.pow(diff=self.diff)

        def __str__(self):
            tmp = self.sign_content()
            tmp['sign'] = self.sign
            return json.dumps(tmp)

        def set_height(self,height):
            self.height = height

        def gethash(self):
            return mycrypto.hash(json.dumps(self.sign_content()))

        def append(self, new_data):
            self.data.extend(new_data)

        def flesh(self, height=None,prevHash = ""):
            if height:
                self.height = height
                for i in range(len(self.data)):
                    # da['LastOperateHeight'] = height
                    self.data[i]['currentHeight'] = height
                    c = Certificate()
                    c.load_dict(self.data[i])
                    c.init()
                    self.data[i] = c.__dict__
                    print("hash check",c.hash,self.data[i]["hash"])
            self.prevBlockHash = prevHash
            self.timeStamp = time.time()
            self.merkleTree = MerkleTree(self.data)
            self.nonce = 0

        def pow(self, diff=5):
            if self.verify(diff):
                return True
            else:
                self.nonce += 1
                return False
            return True

        def verify(self, diff):
            return int(self.gethash()[0:diff], 16) == 0

        def init_from_json(self, js):
            if isinstance(js,str):
                _imported_dict = json.loads(js)
            else:
                _imported_dict = js
            self.height = _imported_dict['height']
            self.version = _imported_dict['version']
            self.nonce = _imported_dict['nonce']
            self.sign = _imported_dict['sign']
            self.diff = _imported_dict['diff']
            self.data = _imported_dict['data']
            self.prevBlockHash = _imported_dict['prevBlockHash']
            self.timeStamp = _imported_dict['timeStamp']
            self.merkleTree = MerkleTree(self.data)

            return self.merkleTree.check(_imported_dict['merkleTree'])

        def sign_content(self):
            tmp = {
                'height':   self.height,
                'version':  self.version,
                'nonce':    self.nonce,
                'diff':     self.diff,
                'data':     self.data,
                'prevBlockHash': self.prevBlockHash,
                'timeStamp':    self.timeStamp,
                'merkleTree':   self.merkleTree
            }
            return tmp

# Merkle Tree
class MerkleTree(list):

    def __init__(self, data):
        total, leaf_start = get2pow(len(data))
        super(MerkleTree,self).__init__(['']*total)

        ii = leaf_start
        for each in data:
            print(data)
            c = Certificate()
            c.load_dict(each)
            c.init()
            self[ii] = c.hash
            ii += 1

        p = leaf_start - 1
        end = len(self) - 1

        while p >= 0:
            self[p] = self.optc(self[end] + self[end - 1])
            p -= 1
            end -= 2

    def optc(self,elem):
        return mycrypto.hash(str(elem))
        #return elem

    def check(self,li):
        # li is a merkel tree imported into a new block
        idx = len(self) - 1
        while idx >= 0:
            if self[idx] != li[idx]:
                return idx
            idx -= 1
        return -1



def get2pow(l):
    h = 1
    while h < l:
        h *= 2

    # tmp = []
    # tmp.append(l)
    # while tmp[-1] != 1:
    #     tmp.append(int(tmp[-1]/2 + 0.5))
    #     total = sum(tmp)
    return 2*h - 1, h - 1


if __name__ == '__main__':
    print(MerkleTree([1,2,3,4,5]))
