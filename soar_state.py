from collections import defaultdict
import re


NODE_PATTERN = re.compile("\((\w\d+)(([ \n]+\^([!-~]+)[ \n]+([!-~ ]+))*)\)")
ATTRIBUTE_PATTERN = re.compile("\^([\w\d\-_]+)\s+([\w\d\-_*.]+|\|.*\|)")


class SoarState(object):
    def __init__(self) -> None:
        self.node_ids = set()
        self.nodes = defaultdict(lambda: defaultdict(list))

    def parse_state_text(self, state_text):
        self.node_ids.clear()
        self.nodes.clear()

        node_matches = re.finditer(NODE_PATTERN, state_text)
        for node_match in node_matches:
            node_text = node_match.group(0)
            node_id = node_match.group(1)
            self.node_ids.add(node_id)
            
            attr_matches = re.finditer(ATTRIBUTE_PATTERN, node_text)
            for attr_match in attr_matches:
                attr_name = attr_match.group(1)
                attr_val = attr_match.group(2)
                self.nodes[node_id][attr_name].append(attr_val)

    def iter(self, node_id="S1", parent="", visited=set()) -> tuple[str, str, str]:
        visited_nodes = set().union(visited)
        visited_nodes.add(node_id)
        active_node = node_id

        attrs = self.nodes[active_node]
        for attr, vals in attrs.items():
            for val in vals:
                if val not in self.node_ids:
                    yield active_node, attr, val, False
                else:
                    if val not in visited_nodes:
                        yield active_node, attr, val, True
                        yield from self.iter(node_id=val, parent=active_node, visited=visited_nodes)
                    else:
                        yield active_node, attr, val, False

    def insert_in_treeview(self, treeview, node_id="S1", parent_tree_id="S1", visited=set()):
        visited_nodes = set().union(visited)
        visited_nodes.add(node_id)
        active_node = node_id

        attrs = self.nodes[active_node]
        for attr, vals in attrs.items():
            for val in vals:
                if val not in self.node_ids:
                    treeview.insert(parent_tree_id, 'end', text=attr, values=(val,))
                else:
                    new_tree_id = treeview.insert(parent_tree_id, 0, text=attr, values=(val,))
                    if val not in visited_nodes:
                        self.insert_in_treeview(treeview, node_id=val, parent_tree_id=new_tree_id, visited=visited_nodes)


if __name__ == "__main__":
    demo_text =\
"""(S1 ^epmem E1 ^io I1
       ^name agent_gamma ^operator O2 + ^reward-link R1 ^smem L1
       ^superstate nil ^svs V1 ^top-state S1 ^type state)
  (E1 ^command C1 ^present-id 1 ^result R2)
  (I1 ^input-link I2 ^output-link I3)
  (O2 ^name create-vog)
  (L1 ^command C2 ^result R3)
  (V1 ^command C3 ^spatial-scene I4 ^vltm V3 ^vsm V4 ^vwm V2)
    (I4 ^id world)
    (V4 ^size 0 ^visual-buffer V5 ^vog V6)
      (V5 ^frames F1 ^newest-update 32649 ^oldest-update 0 ^size 0)
"""
    nodes = re.finditer(NODE_PATTERN, demo_text)
    for n in nodes:
        node_text = n.group(0)
        print(node_text)
        attrs = re.finditer(ATTRIBUTE_PATTERN, node_text)
        for a in attrs:
            print(f"\t{a.group(1)} = {a.group(2)}")

    state = SoarState()
    state.parse_state_text(demo_text)
    for n in state.iter():
        print(n)
