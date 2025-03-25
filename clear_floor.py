import argparse
import os
from lxml import etree
from itertools import chain
from tqdm import tqdm
import glob 
from svgnet.data.svg import SVG_CATEGORIES


CLASS_NAMES = {x["id"] : x["name"] for x in SVG_CATEGORIES}
CLASS_NAMES.update({0 : "UNKNOWN"})


def get_args():
    """Parses command-line arguments for the SVGNet inference script.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser("svgnet")
    parser.add_argument(
        "--input_dir",
        type=str,
        help="Directory for input",
        default="./visualise_outputs_jem",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory for output results.",
        default="./clean_results",
    )
    
    args = parser.parse_args()
    return args


def clear_xml(svg_file, out_folder):
    tree = etree.parse(svg_file)
    root = tree.getroot()
    ns = root.tag[:-3] # Extracts XML namespace from root tag

    keep_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 28, 33, 34]
    keep_ids = list(map(str, keep_ids))

    remove_count = {i: 0 for i in range(37) if str(i) not in keep_ids}
    keep_count = {int(i): 0 for i in keep_ids}

    keep_count 
    to_remove = {}
    for g in root.iter(ns + "g"):  # Iterates through all <g> (group) elements in the SVG
        # Looks for path, circle and ellipse
        for _path in chain(
            g.iter(ns + "path"), 
            g.iter(ns + "circle"), 
            g.iter(ns + "ellipse")
        ):
            
            if "semanticId" in _path.attrib:
                id = _path.attrib["semanticId"]
                if not(id in keep_ids):
                    to_remove.update({_path : int(id)})
                else:
                    keep_count[int(id)] += 1
        
    for path, id in to_remove.items(): 
        parent = path.getparent()
        if parent is not None:
            parent.remove(path)
            remove_count[id] += 1


    for id, count in remove_count.items(): print(f"Class {id} : {CLASS_NAMES[id]}, {count} elements removed")
    for id, count in keep_count.items(): print(f"Class {id} : {CLASS_NAMES[id]}, {count} elements found and kept")
    tree.write(os.path.join(out_folder, os.path.basename(svg_file)))

def process():
    args = get_args()
    os.makedirs(args.input_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    svg_paths = glob.glob(os.path.join(args.input_dir,'*.svg'))
    print(f"{args.input_dir}")
    for file in tqdm(svg_paths):
        print(f"File {file}")
        clear_xml(file, args.output_dir)
        print(f"-------------------------------------------------------------------")

def main():
    process()

if __name__ == "__main__":
    main()