import os
import json
from services.svg_loader import load_optimized_svg
from services.annotation_cleaner import remove_annotations
from services.json_parser import parse_svg
from services.svg_serializer import process
def cad_workflow(svg_file):
    basename = os.path.basename(test_file)
    json_basename = basename.replace(".svg",".json")
    project_name =  os.path.splitext(basename)[0]

    dataset_path=f"/mnt/c/Dataset/{project_name}/svg"
    json_path=f"/mnt/c/Dataset/{project_name}/json"
    output_path=f"/mnt/c/Dataset/{project_name}/result"

    os.makedirs(dataset_path,exist_ok=True)
    os.makedirs(json_path,exist_ok=True)
    os.makedirs(output_path,exist_ok=True)

    optimized_tree = load_optimized_svg(svg_file)
    no_annotations_tree = remove_annotations(optimized_tree)
    json_repr = parse_svg(no_annotations_tree)


    tree_file = os.path.join(dataset_path, basename)
    json_file = os.path.join(json_path, json_basename)

    no_annotations_tree.write(tree_file)
    json.dump(json_repr, open(json_file, 'w'), indent=4)

    #process(json_path, dataset_path, output_path)

    #output_file = os.path.join(output_path, basename)
    return tree_file

def main(test_file):
    cad_workflow(test_file)


if __name__ == "__main__":
    test_file = "./dataset/test/test/raw/1-Crosby_Original_Model.svg"
    main(test_file)