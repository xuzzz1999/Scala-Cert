###########################################################
# Package: BlockChain
# Filename: core
# Time: Apr 26, 2019 at 3:37:50 PM
############################################################

import json
from .node import Node, NodeAddr, ConsenseMethod
import threading,socket

with open("config/master.json","r") as f:
    config = json.load(f)

node = Node(config)

print(node)