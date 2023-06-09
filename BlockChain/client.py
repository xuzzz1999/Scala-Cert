import socket
import json

def sender(addr, msg):
    try:
        s = socket.socket()
        s.connect((addr["ip"], int(addr["port"])))
        s.send(bytes(msg, encoding="utf-8"))
        ret = str(s.recv(6553500), encoding="utf-8")
        _,body = loadjson(ret)
        s.close()
    except ConnectionRefusedError as e:
        return "Error"
    return body


def broadcast(peers, msg):
    rets = []
    for peer in peers:
        rets.append(sender(peer,msg))
    return rets


def dumpjson(url,body):
    msg = {"url": url, "body": body}
    return json.dumps(msg)


def loadjson(msg):
    obj = json.loads(msg)
    return obj["url"], obj["body"]


def isconse(a,b):
    if b == 0:
        return False
    return a/b > 2/3
