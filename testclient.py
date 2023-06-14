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
    crk,cpk = mycrypto.open_ckey("keys/node1_cpriv_cer","keys/node1_cpub_cer")
    print("-----start create a certificate!")
    c = Certificate(serial = "1",subject = str(count), pub_key = "23333",proxyServer = "client1",pk=cpk)
    li.append(count)

    c.create_certificate(priv_key)
    print("-----send: {}".format(c.get_js()))
    print("-----after send")
    broadcast(peers, dumpjson("add", c.get_js()))
    time.sleep(10)

    ret = sender(peers[0],dumpjson("search", {"subject": str(li[0])}))

    for ce in ret:
            c = Certificate()
            print(ce)
            c.load_dict(ce)
            print("-----certificate query")
            print("-----Certificate {} is found".format(c.subject))
            lasth = c.currentHeight
            print(c.get_js())
            # try:
            #     li.remove(int(c.subject))
            # except:
            #     pass

    c = Certificate(serial = "1",subject = str(count),types= "Revoke", pub_key = "23333",proxyServer = "client1",LastOperateHeight=lasth, pk=cpk)
    c.create_certificate(priv_key)
    print("-----send: {}".format(c.get_js()))
    broadcast(peers, dumpjson("add", c.get_js()))    
    
    logging.info('continue')
    
    time.sleep(10) 
    print("-----start revoke certificate")
    ret = sender(peers[0],dumpjson("search", {"subject": str(li[0])}))     
    for ce in ret:
            c = Certificate()
            print(ce)
            c.load_dict(ce)
            # print("-----after revoke")
            print("-----Certificate {} is found".format(c.subject))
            print(c.get_js())
            print(c.opercheck())
            try:
                li.remove(int(c.subject))
            except:
                pass

  logging.info('finish')
