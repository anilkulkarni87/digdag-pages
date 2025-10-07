
from typing import List
from uuid import uuid4
from graphviz import Digraph

def no_escape(text: str) -> str:
    return text

class Block:
    def __init__(self, graph_name: str, label: str, color: str, penwidth: float = 1.0, 
                 URL: str = "", shape: str = "box", tooltip: str = ""):
        self.graph_name = graph_name
        self.name = str(uuid4())
        self.label = label
        self.color = color
        self.penwidth = penwidth
        self.URL = URL
        self.shape = shape
        self.tooltip = tooltip
        self.subblocks: List['Block'] = []
        self.subgraph_name = f"cluster-{uuid4()}"
        self.parallel = False

    def append(self, label: str, color: str = "", penwidth: float = 1.0, 
               shape: str = "box", URL: str = "", tooltip: str = "") -> 'Block':
        block = Block(self.subgraph_name, label, color=color, penwidth=penwidth,
                      URL=URL, shape=shape, tooltip=tooltip)
        self.subblocks.append(block)
        return block

    def last(self) -> List['Block']:
        if self.subblocks:
            if self.parallel:
                res = []
                for block in self.subblocks:
                    res += block.last()
                return res
            else:
                return self.subblocks[-1].last()
        return [self]

    def draw(self, dot: Digraph) -> None:
        dot.node(
            self.name,
            no_escape(self.label),
            color=self.color,
            penwidth=str(self.penwidth),
            shape=self.shape,
            URL=self.URL,
            tooltip=no_escape(self.tooltip)
        )
        prev = [self]
        with dot.subgraph(name=self.subgraph_name) as c:
            for block in self.subblocks:
                block.draw(c)
                for b in prev:
                    dot.edge(b.name, block.name)
                if not self.parallel:
                    prev = block.last()
