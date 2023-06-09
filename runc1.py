import socket
import time
import random
from BlockChain.client import *
from BlockChain.node import NodeAddr
from BlockChain.certificate import *

dic = [
    {'ip': "127.0.0.1", 'port': 6000},
    {'ip': "127.0.0.1", 'port': 6002},
    {'ip': "127.0.0.1", 'port': 6004},
]

peers = []

count = 0

def init_peers():
    for peer in dic:
        peers.append(NodeAddr(peer))

def send_data():
    global count
    print("send: {}".format(str(count)))
    broadcast(peers, dumpjson("add", str(count)))
    count += 1

if __name__ == "__main__":
    li = []
    init_peers()
    uug.change_addr('client1')
    priv_key,_ = mycrypto.open_key("keys/client1_priv.cer", "keys/client1_pub.cer")
    while True:
        c = Certificate(subject = str(count), pub_key = "23333",proxyServer = "client1")
        li.append(count)
        count += 1
        c.create_certificate(priv_key)
        # print("send: {}".format(c.get_js()))
        broadcast(peers, dumpjson("add", c.get_js()))
        time.sleep(5)

        ret = sender(peers[0],dumpjson("search", {"subject": str(li[0])}))
        for ce in ret:
            c = Certificate()
            print(ce)
            c.load_dict(ce)
            print("Certificate {} is found".format(c.subject))
            print(c.get_js())
            try:
                li.remove(int(c.subject))
            except:
                pass
                
    # while True:
    #     send_data()
    #     time.sleep(5)