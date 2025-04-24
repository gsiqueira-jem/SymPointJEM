import os
import sys
import json
import logging
from services.svg_loader import load_optimized_svg
from services.annotation_cleaner import remove_annotations
from services.json_parser import parse_svg
from services.svg_serializer import process
from services.remove_segments import clear_xml

def cad_workflow(svg_file, task_dir, logger, scour=False):
    basename = os.path.basename(svg_file)
    json_basename = basename.replace(".svg",".json")
    project_name =  os.path.splitext(basename)[0]
    
    logger.info("Creating output dirs for task")
    dataset_path=f"/mnt/c/Dataset/{project_name}/clear_annotations"
    json_path=f"/mnt/c/Dataset/{project_name}/json"
    reconstructed_path=f"/mnt/c/Dataset/{project_name}/reconstructed"
    output_path=f"/mnt/c/Dataset/{project_name}/final"


    os.makedirs(dataset_path,exist_ok=True)
    os.makedirs(json_path,exist_ok=True)
    os.makedirs(reconstructed_path,exist_ok=True)
    os.makedirs(output_path,exist_ok=True)

    logger.info("Optimizing SVG and Breaking Polylines")
    optimized_tree = load_optimized_svg(svg_file, task_dir, logger, scour=scour)
    logger.info("SVG Optimized and polylines broken into paths")


    logger.info("Removing Annotations from file")
    no_annotations_tree = remove_annotations(optimized_tree, logger)
    logger.info("Annotations removed")

    # logger.info("Creating json representation")
    json_repr = parse_svg(no_annotations_tree)


    tree_file = os.path.join(dataset_path, basename)
    json_file = os.path.join(json_path, json_basename)

    no_annotations_tree.write(tree_file)
    json.dump(json_repr, open(json_file, 'w'), indent=4)

    process(json_path, dataset_path, reconstructed_path)
    
    reconstructed_file = os.path.join(reconstructed_path, basename)
    clear_xml(reconstructed_file, output_path)
    
    return tree_file


def main(test_file, test_dir, logger):
    cad_workflow(test_file, test_dir, logger)


if __name__ == "__main__":
    test_file = "./dataset/test/test/raw/aspose_no_scour.svg"
    test_dir = "/tmp/test"
    os.makedirs(test_dir+"/scour",exist_ok=True)

    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.DEBUG)  # Or INFO, WARNING, etc.
    console_handler = logging.StreamHandler(sys.stdout)

    # Cria um formato de log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    main(test_file, test_dir, logger)