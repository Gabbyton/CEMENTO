from os import path
import pandas as pd
from cemento.tree import Tree
from cemento.draw_io.write_diagram import WriteDiagram

# NOTE: please run script from root

INPUT_FILE_PATH = "test_cases/in/sample_tree.xlsx"
SAVE_FOLDER_PATH = "test_cases/out/sample_tree"

if __name__ == "__main__":

    excel_sheets =  pd.read_excel(INPUT_FILE_PATH, sheet_name=None)

    for sheet_name, df in excel_sheets.items():
        print(sheet_name)
        sample_tree = Tree(rels_df=df)
        diagram_save_path = path.join(SAVE_FOLDER_PATH, f"{sheet_name}.drawio")
        diagram = WriteDiagram(file_path=diagram_save_path)
        sample_tree.draw_tree(write_diagram=diagram)
        diagram.draw()