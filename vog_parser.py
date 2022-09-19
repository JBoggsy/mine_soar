from collections import defaultdict
import json
import re
import textwrap

import graphviz
import numpy as np
import matplotlib.pyplot as plt

from matrix_viewer import show_matrix_as_heatmap, show_matrix_as_image, show_matrix_as_points


class Node(object):
    def __init__(self, soar_id):
        self.soar_id = soar_id
        self.node_id = -1
        self.node_op = ""
        self.node_name = ""
        self.children = []
        self.parent_dict = {}
        self.attributes = defaultdict(list)
        self.matrix_metadata = {}
        self.matrix = None
        self.__needs_drawing = True
    
    def load_matrix_data(self):
        with open(f"node-{self.node_id}.json", "r") as node_file:
            image_data = json.load(node_file)["Image Data"]
            self.matrix_metadata["data_type"] = image_data['dt']
            if len(self.matrix_metadata["data_type"]) > 1:
                chans = int(self.matrix_metadata["data_type"][0])
            else:
                chans = 1
            
            self.matrix_metadata["shape"] = (image_data['rows'], image_data['cols'], chans)
            self.matrix_metadata["raw_data"] = image_data['data']

        self.matrix = np.array(self.matrix_metadata["raw_data"]).reshape(self.matrix_metadata["shape"])
        self.__needs_drawing = True

    def draw_matrix_data(self):
        if self.matrix is None: return
        if not self.__needs_drawing: return

        if self.node_op in ["save-to-file", "get-from-vsm"]:
            fig, axes = show_matrix_as_image(self.matrix)
        elif self.node_name in ["Dxyz matrix"]:
            fig, axes = show_matrix_as_points(self.matrix)
        else:
            fig, axes = show_matrix_as_heatmap(self.matrix)
        fig.savefig(f"node-{self.node_id}.png")
        plt.close(fig)
        self.__needs_drawing = False

    @property
    def node_label(self):
        wrapped_node_name = "<BR/>".join(textwrap.wrap(self.node_name, 10))

        attrs_list = filter(lambda a: a not in self.parent_dict or self.parent_dict[a] != -1, self.attributes)
        attrs_list = list(filter(lambda a: a not in ["node-id", "op-name", "node-name"], attrs_list))

        ret_str = f"""\
<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
    <TR>
        <TD COLSPAN="2">
            <B>{self.node_name}</B> ({self.node_id})
        </TD>
    </TR>
    <TR>
        <TD><I>{self.node_op}</I></TD>
        <TD PORT="img" ROWSPAN="{len(attrs_list)+1}"><IMG SRC="node-{self.node_id}.png"/></TD>
    </TR>"""

        if len(attrs_list) > 0:
            ret_str += f"""
            {"".join([f'<TR><TD PORT="{a}">{a}={",".join(self.attributes[a])}</TD></TR>' for a in attrs_list])}"""
        
        ret_str += """
</TABLE>>
"""
        print(ret_str)
        return ret_str


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
                elif attr_name == "node-name": node.node_name = attr_val.strip("|")

                node.attributes[attr_name].append(attr_val)
                if attr_name in ["source", "a", "b", "template"]: node.parent_dict[attr_name] = int(attr_val)
                if node.node_op == "save-to-file": node.node_name = "save node"
                
            self.nodes[node.node_id] = node
        
        for n_id, n in self.nodes.items():
            for p_id in n.parent_dict.values():
                self.nodes[p_id].children.append(n_id)
        
        node_key_dict = dict()
        for node_id, node in self.nodes.items():
            node_key_dict[node_id] = dict(node.attributes)
        with open("key.json", "w") as node_key_f:
            json.dump(node_key_dict, node_key_f)

    def draw_graph(self, save_nodes=False, visuals=True):
        graph = graphviz.Digraph(comment="Visual Operation Graph",
                                 node_attr={'shape': 'none'},
                                 format="png",)
        graph.attr(rankdir='LR', ranksep="1.0", minlen="2")
        for node_id, node in self.nodes.items():
            if node_id == -1: continue
            if node.node_op == "save-to-file" and not save_nodes: continue
            if visuals:
                node.load_matrix_data()
                node.draw_matrix_data()
            graph.node(str(node_id), node.node_label)

        for node_id, node in self.nodes.items():
            if node_id == -1: continue
            if node.node_op == "save-to-file" and not save_nodes: continue
            for attr_name, p_id in node.parent_dict.items():
                if p_id == -1: continue
                graph.edge(f"{p_id}:img:e", f"{node_id}:{attr_name}:w")
        graph.render("visual_operation_graph", view=True)



if __name__ == "__main__":
    test_text = """(V6 ^node N42 ^node N41 ^node N40 ^node N39 ^node N38 ^node N37 ^node N36
       ^node N35 ^node N34 ^node N33 ^node N32 ^node N31 ^node N30 ^node N29
       ^node N28 ^node N27 ^node N26 ^node N25 ^node N24 ^node N23 ^node N22
       ^node N21 ^node N20 ^node N19 ^node N18 ^node N17 ^node N16 ^node N15
       ^node N14 ^node N13 ^node N12 ^node N11 ^node N10 ^node N9 ^node N8
       ^node N7 ^node N6 ^node N5 ^node N4 ^node N3 ^node N2 ^node N1)
  (N42 ^a 40 ^b 35 ^node-id 41 ^node-name |Dxyz matrix|
         ^op-name stack-matrices ^source -1)
  (N41 ^a 38 ^b 32 ^node-id 40 ^node-name |Dxy matrix| ^op-name stack-matrices
         ^source -1)
  (N40 ^filepath |node-38-image.png| ^node-id 39 ^op-name save-to-file
         ^source 38)
  (N39 ^a 20 ^b 37 ^node-id 38 ^node-name |Dx matrix| ^op-name mul-mats
         ^source -1)
  (N38 ^node-id 37 ^node-name |Vx matrix| ^op-name apply-unary-op ^source 31
         ^unary-op negate)
  (N37 ^filepath |node-35-image.png| ^node-id 36 ^op-name save-to-file
         ^source 35)
  (N36 ^a 20 ^b 34 ^node-id 35 ^node-name |Dz matrix| ^op-name mul-mats
         ^source -1)
  (N35 ^a 24 ^b 29 ^node-id 34 ^node-name |Vz matrix| ^op-name mul-mats
         ^source -1)
  (N34 ^filepath |node-32-image.png| ^node-id 33 ^op-name save-to-file
         ^source 32)
  (N33 ^a 20 ^b 28 ^node-id 32 ^node-name |Dy matrix| ^op-name mul-mats
         ^source -1)
  (N32 ^a 24 ^b 30 ^node-id 31 ^node-name |neg Vx matrix| ^op-name mul-mats
         ^source -1)
  (N31 ^node-id 30 ^node-name |sin yaw matrix| ^op-name apply-unary-op
         ^source 25 ^unary-op sin)
  (N30 ^node-id 29 ^node-name |cos yaw matrix| ^op-name apply-unary-op
         ^source 25 ^unary-op cos)
  (N29 ^node-id 28 ^node-name |Vy matrix| ^op-name apply-unary-op ^source 27
         ^unary-op negate)
  (N28 ^node-id 27 ^node-name |sin pitch matrix| ^op-name apply-unary-op
         ^source 22 ^unary-op sin)
  (N27 ^filepath |node-25-image.png| ^node-id 26 ^op-name save-to-file
         ^source 25)
  (N26 ^a 19 ^b 16 ^node-id 25 ^node-name |yaw matrix| ^op-name add-mats
         ^source -1)
  (N25 ^node-id 24 ^node-name |cos pitch matrix| ^op-name apply-unary-op
         ^source 22 ^unary-op cos)
  (N24 ^filepath |node-22-image.png| ^node-id 23 ^op-name save-to-file
         ^source 22)
  (N23 ^a 18 ^b 4 ^node-id 22 ^node-name |pitch matrix| ^op-name add-mats
         ^source -1)
  (N22 ^filepath |node-20-image.png| ^node-id 21 ^op-name save-to-file
         ^source 20)
  (N21 ^channel 3 ^node-id 20 ^node-name |D matrix| ^op-name extract-channel
         ^source 8)
  (N20 ^a 15 ^b 0 ^node-id 19 ^node-name |yaw adj matrix| ^op-name sub-mats
         ^source -1)
  (N19 ^a 14 ^b 7 ^node-id 18 ^node-name |pitch adj matrix| ^op-name sub-mats
         ^source -1)
  (N18 ^filepath |node-16-image.png| ^node-id 17 ^op-name save-to-file
         ^source 16)
  (N17 ^fill-val 0.000000 ^node-id 16 ^node-name |agent yaw matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
  (N16 ^a 12 ^b 11 ^node-id 15 ^node-name |raw yaw adj matrix|
         ^op-name mul-mats ^source -1)
  (N15 ^a 13 ^b 10 ^node-id 14 ^node-name |raw pitch adj matrix|
         ^op-name mul-mats ^source -1)
  (N14 ^a 2 ^b 3 ^node-id 13 ^node-name |vert pct matrix| ^op-name div-mats
         ^source -1)
  (N13 ^a 1 ^b 6 ^node-id 12 ^node-name |horiz pct matrix| ^op-name div-mats
         ^source -1)
  (N12 ^fill-val 86.100000 ^node-id 11 ^node-name |Fh matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
  (N11 ^fill-val 70.000000 ^node-id 10 ^node-name |Fv matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
  (N10 ^filepath |node-8-image.png| ^node-id 9 ^op-name save-to-file ^source 8)
  (N9 ^node-id 8 ^node-name vision ^op-name get-from-vsm ^source -1
         ^vsm -840661560)
  (N8 ^fill-val 35.000000 ^node-id 7 ^node-name |Fv/2 matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
  (N7 ^fill-val 640.000000 ^node-id 6 ^node-name |W matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
  (N6 ^filepath |node-4-image.png| ^node-id 5 ^op-name save-to-file ^source 4)
  (N5 ^fill-val 0.000000 ^node-id 4 ^node-name |agent pitch matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
  (N4 ^fill-val 480.000000 ^node-id 3 ^node-name |H matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
  (N3 ^node-id 2 ^node-name |y matrix| ^op-name create-y-coord-mat ^size-x 640
         ^size-y 480 ^source -1)
  (N2 ^node-id 1 ^node-name |x matrix| ^op-name create-x-coord-mat ^size-x 640
         ^size-y 480 ^source -1)
  (N1 ^fill-val 43.050000 ^node-id 0 ^node-name |Fh/2 matrix|
         ^op-name create-float-filled-mat ^size-x 640 ^size-y 480 ^source -1)
"""
    
    vog = VOG()
    vog.parse_vog_text(test_text)
    vog.draw_graph()