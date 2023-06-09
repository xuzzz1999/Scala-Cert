from BlockChain.node import Node
import json

with open("config/node2.json","r") as f:
    config = json.load(f)

node = Node("node2",config)
node.run()