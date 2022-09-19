from collections import defaultdict
import json
import re


class Node(object):
    def __init__(self, soar_id):
        self.soar_id = soar_id
        self.node_id = -1
        self.node_op = ""
        self.node_name = ""
        self.children = []
        self.parent_dict = {}
        self.attributes = defaultdict(list)
        self.matrix_data = None
    
    def load_matrix_data(self):
        with open(f"node-{self.node_id}.json", "r") as node_file:
            self.matrix_data = json.load(node_file)["Image Data"]

        

class VOG(object):
    NODE_PATTERN = re.compile("\((\w\d+)(([ \n]+\^([!-~]+)[ \n]+([!-~ ]+))*)\)")
    ATTRIBUTE_PATTERN = re.compile("\^([\w\d\-_]+)\s+([\w\d\-_*.]+|\|.*\|)")

    def __init__(self):
        self.nodes = {-1: Node("V6")}
    
    def parse_vog_text(self, vog_text):
        node_matches = re.finditer(VOG.NODE_PATTERN, vog_text)
        for node_match in node_matches:
            soar_id = node_match[1]
            node_attr_text = node_match[2].strip()
            attr_matches = re.finditer(VOG.ATTRIBUTE_PATTERN, node_attr_text)

            node = Node(soar_id)
            for attr_match in attr_matches:
                attr_name = attr_match[1]
                attr_val = attr_match[2]
                
                if attr_name == "node-id": node.node_id = int(attr_val)
                elif attr_name == "op-name": node.node_op = attr_val
                elif attr_name == "node-name": node.node_name = attr_val
                node.attributes[attr_name].append(attr_val)
                if attr_name in ["source", "a", "b", "template"]: node.parent_dict[attr_name] = int(attr_val)
                
            self.nodes[node.node_id] = node
        
        for n_id, n in self.nodes.items():
            for p_id in n.parent_dict.values():
                self.nodes[p_id].children.append(n_id)
        
        node_key_dict = dict()
        for node_id, node in self.nodes.items():
            node_key_dict[node_id] = dict(node.attributes)
        with open("key.json", "w") as node_key_f:
            json.dump(node_key_dict, node_key_f)



if __name__ == "__main__":
    test_text = """(V6 ^node N4 ^node N3 ^node N2 ^node N1)
  (N4 ^fill-val 70.000000 ^node-id 3 ^node-name |Fv matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^target -1)
  (N3 ^node-id 2 ^node-name |y matrix| ^op-name create-y-coord-mat ^size-x 640
         ^size-y 480 ^target -1)
  (N2 ^fill-val 35.000000 ^node-id 1 ^node-name |Fv/2 matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^target -1)
  (N1 ^node-id 0 ^node-name |x matrix| ^op-name create-x-coord-mat ^size-x 640
         ^size-y 480 ^target -1)"""
    
    vog = VOG()
    vog.parse_vog_text(test_text)
    print(str(vog))