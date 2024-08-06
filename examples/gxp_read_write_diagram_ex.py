from cemento.tree import Tree

from cemento.draw_io.read_diagram import ReadDiagram
from cemento.draw_io.write_diagram import WriteDiagram

# NOTE: please run script from root

INPUT_PATH = "test_cases/in/ref_diagram.drawio"
OUTPUT_PATH = "test_cases/out/ref_diagram_fixed.drawio"

if __name__ == "__main__":
    read_diagram = ReadDiagram(file_path=INPUT_PATH)
    rel_df = read_diagram.get_relationships()

    print(rel_df.iloc[:,-4:])

    sample_tree = Tree(rels_df=rel_df)
    draw_diagram = WriteDiagram(OUTPUT_PATH)
    sample_tree.draw_tree(draw_diagram)
    draw_diagram.draw()