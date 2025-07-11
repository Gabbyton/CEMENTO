from cemento.rdf.read_turtle import ReadTurtle
from cemento.tree import Tree
from cemento.draw_io.write_diagram import WriteDiagram

INPUT_PATH = "<INSERT-PATH-HERE>"
OUTPUT_PATH = "<INSERT-PATH-HERE>"

if __name__ == "__main__":
    ex = ReadTurtle(INPUT_PATH)
    tree = Tree(graph=ex.get_graph(), do_gen_ids=True, invert_tree=True)
    diagram = WriteDiagram(OUTPUT_PATH)
    tree.draw_tree(write_diagram=diagram)
    diagram.draw()