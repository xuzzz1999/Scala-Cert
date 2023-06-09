from BlockChain.node import Node
import json

with open("config/node1.json","r") as f:
    config = json.load(f)

node = Node("node1",config)
node.run()