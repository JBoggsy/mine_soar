from pprint import pprint
import re


class Node(object):
    def __init__(self, soar_id):
        self.soar_id = soar_id
        self.node_id = -1
        self.node_op = ""
        self.children = []
        self.parent_dict = {}
        self.attributes = []

        

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
                else: node.attributes.append((attr_name, attr_val))
                if attr_name in ["target", "a", "b", "template"]: node.parent_dict[attr_name] = int(attr_val)
                
            self.nodes[node.node_id] = node
        
        for n_id, n in self.nodes.items():
            for p_id in n.parent_dict.values():
                self.nodes[p_id].children.append(n_id)

    def __str__(self):
        ret_str = ""
        node_stack = [(-1,0)]
        while len(node_stack) > 0:
            active_node_id, depth = node_stack.pop()
            ret_str += "|" + "---"*(depth)
            active_node = self.nodes[active_node_id]
            active_node_op = "root" if active_node_id == -1 else active_node.node_op
            ret_str += f"{active_node_id}: {active_node_op}\n"
            for attr_name, attr_val in active_node.attributes:
                ret_str += "|" + "---"*(depth)
                ret_str += f"---{attr_name}={attr_val}\n"
            for c_id in active_node.children:
                node_stack.append((c_id, depth+1))
        return ret_str



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