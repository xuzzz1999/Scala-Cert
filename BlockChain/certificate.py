import time
import random
import json
from datetime import datetime,timedelta
from dataclasses import dataclass, field
from BlockChain import mycrypto
# import gmpy2

p = 0x10000000000000000000000000000000000000000000000000000000000000129
g = 5

@dataclass
class UUIDGenerator(object):
    name: str = "node"
    count: int = 0
    salt: str = "salt123"

    def change_addr(self,name, salt = "salt123"):
        self.name = name
        self.salt = salt
    
    def get_uuid(self):
        self.count += 1
        return self.name + \
        str(int(time.time() * 100000)) + \
        mycrypto.hash( str(self.count) + self.salt)

uug = UUIDGenerator()

def factory_not_before():
    return datetime.now().timestamp()

def factory_not_after():
    now = datetime.now()
    notafter = now + timedelta(days = 365) 
    return notafter.timestamp()

@dataclass
class Certificate(object):

    version: int = 1    # Version Number
    serial: str = field(default_factory=uug.get_uuid)    # Serial Number
    types:  str = "Create" # Type: Create or Revoke or Update
    algorithm: str = "rsa1024" # Algorithm
    proxyServer: str = ""
    notBefore: any = field(default_factory=factory_not_before)
    notAfter: any = field(default_factory=factory_not_after)
    subject: str = "1231231231" # phone or email
    pub_key: str = field(default="123")
    publicKeyAlgorithm: str = "rsa1024"
    Signature: str = field(default= '',repr = False)
    timeStamp: any = field(default_factory=factory_not_before)
    currentHeight: int = field(default= -1,repr = True)
    LastOperateHeight: int = field(default= -1,repr = True)
    pk: int = 0
    hash: any = None
    nonce: any = None

    def get_js(self):
        # 获取所以属性的 json 字符串，用于传输
        return json.dumps(self.__dict__)
    
    def sign_content(self):
        content = str(self.version)+str(self.serial)+ \
        str(self.types)+str(self.algorithm)+str(self.proxyServer)+str(self.notAfter)+str(self.notBefore)+str(self.subject) \
            +str(self.pub_key)+str(self.publicKeyAlgorithm)+str(self.Signature)+str(self.timeStamp)+str(self.currentHeight)+str(self.LastOperateHeight)
        return content

    def load_json(self,js):
        self.__dict__ = json.loads(js)
    
    def load_dict(self,di):
        self.__dict__ = di

    def create_certificate(self, priv_key):
        hashcert = mycrypto.hash(self.sign_content())
        sign = mycrypto.sign(priv_key, hashcert)
        self.Signature = sign

    def search_by_subject(self, sub):
        if sub == self.subject:
            return self
        else:
            return None

    def search_by_uuid(self, id):
        if id == self.serial:
            return self
        else:
            return None

    def __eq__(self, other):
        return self.subject == other.subject and self.serial == other.serial

    def init(self):
        if self.types == "Create":
            ha,rand = mycrypto.chash(self.pk,self.sign_content())
            self.nonce = rand
            self.hash = ha
        else:
            self.hash = mycrypto.hash(self.sign_content())

    def opercheck(self):
        if self.types == "Create":
            return mycrypto.check(self.pk,self.sign_content(),self.nonce,self.hash)
        else :
            return self.hash == mycrypto.hash(self.sign_content())
    
    def modify_height(self,height,privk):
        if pow(g,privk,p) == self.pk:
            msg = self.sign_content()
            self.LastOperateHeight = height
            self.nonce = mycrypto.adapt(privk,msg,self.nonce,self.sign_content())
        else:
            print("wrong private key")


if __name__ == "__main__":
    pk = 37601330523044500144478344601312356175492042275888859976404364015752928230276
    rk = 100262767867775254331348631889683216606266395407701864754674176477564705846571
    c = Certificate(serial = "1",subject = str(1), pub_key = "23333",proxyServer = "client1",pk = pk)
    c.init()
    print(c.modify_height(166,rk))
    print(c.opercheck())
    print(c)