from BlockChain.node import Node
import json

with open("config/node3.json","r") as f:
    config = json.load(f)

node = Node("node3",config)
node.run()