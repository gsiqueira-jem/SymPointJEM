from scour.scour import start as scour, parse_args as scour_args, getInOut as scour_io
from io import BytesIO
from lxml import etree
import os
import glob
import argparse
from tqdm import tqdm
from math import hypot
import re

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
        default="../dataset/test/test/raw",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory for output results.",
        default="../dataset/test/test/svg_gt",
    )
    
    args = parser.parse_args()
    return args


def points_to_path(points_str, closed=False):
    nums = list(map(float, points_str.strip().replace(',', ' ').split()))
    coords = list(zip(nums[::2], nums[1::2]))
    if not coords:
        return ""
    
    new_coords = [coords[0]]
    for c in coords[1:]:
        p = new_coords[-1]
        if c != p:
            new_coords.append(c)

    if len(new_coords) <= 1:
        return ""
    
    d = "M " + " L ".join(f"{x} {y}" for x, y in coords)
    
    if closed:
        d += " Z"
    return d

import re

def collapse_dattr(d_attr):
    if not d_attr:
        return ''

    tokens = re.findall(r'[a-zA-Z]|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?', d_attr)
    cleaned_tokens = []
    i = 0
    prev_point = None

    while i < len(tokens):
        cmd = tokens[i]
        cmd = cmd.upper()

        if cmd == 'M' or cmd == 'L':
            try:
                x = float(tokens[i + 1])
                y = float(tokens[i + 2])
                current_point = (x, y)

                if cmd == 'M':
                    cleaned_tokens.extend(['M', str(x), str(y)])
                    prev_point = current_point
                elif cmd == 'L':
                    if current_point != prev_point:
                        cleaned_tokens.extend(['L', str(x), str(y)])
                        prev_point = current_point

                i += 3
            except (IndexError, ValueError):
                break
        else:
            # For unhandled commands, just pass them through
            cleaned_tokens.append(tokens[i])
            i += 1

    return ' '.join(cleaned_tokens)


def is_trivial_path(d_attr):
    if not d_attr:
        return True

    tokens = re.findall(r'[a-zA-Z]|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?', d_attr)


    # Case 1: Just a move command — useless
    if len(tokens) == 3 and tokens[0].upper() == 'M':
        return True

    # Case 2: Move followed by a line to same point
    if len(tokens) == 6 and tokens[0].upper() == 'M' and tokens[3].upper() == 'L':
        try:
            x1, y1 = float(tokens[1]), float(tokens[2])
            x2, y2 = float(tokens[4]), float(tokens[5])
            return x1 == x2 and y1 == y2
        except ValueError:
            return False

    return False


def poly2path(tree, logger):
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    no_info = 0
    trivial = 0

    for tag_name in ['polyline', 'polygon']:
        elements = root.xpath(f'//svg:{tag_name}', namespaces=ns)
        closed = tag_name == 'polygon'
        print(f"{len(elements)} {tag_name}s to clean")
        for elem in elements:
            points = elem.get('points')
            if not points:
                no_info +=1
                continue

            d = points_to_path(points, closed=closed)
            if not d:
                parent = elem.getparent()
                parent.remove(elem)
                trivial += 1
                continue

            # Create new <path> element
            new_elem = etree.Element('path')
            new_elem.set('d', d)

            # Copy style/presentation attributes
            for attr in elem.attrib:
                if attr not in ['points']:
                    new_elem.set(attr, elem.get(attr))

            # Replace the old element with new one
            parent = elem.getparent()
            parent.replace(elem, new_elem)
    
    logger.info(f"{no_info} polylines/polygons skipped because of no info")
    logger.info(f"{trivial} polylines/polygons skipped because of being 0 length")

    return tree

def remove_trivial_paths(tree, logger):
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    paths = tree.xpath(f'//svg:path', namespaces=ns)

    removed = 0
    for path in paths:
        d = path.get("d")
        new_d = collapse_dattr(d)
        if new_d:
            path.set("d", new_d)
        else:
            path.getparent().remove(path)
            removed +=1
    logger.info(f"Removed {removed} paths for being size 0")
    return tree

def poly2path_indisk(svg_file, out_folder):
    tree = etree.parse(svg_file)
    tree = poly2path(tree)
    tree.write(os.path.join(out_folder, os.path.basename(svg_file)))

def process():
    args = get_args()
    os.makedirs(args.input_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    svg_paths = glob.glob(os.path.join(args.input_dir,'*.svg'))
    print(f"{args.input_dir}")
    for file in tqdm(svg_paths):
        print(f"File {file}")
        poly2path_indisk(file, args.output_dir)

def get_scour_params(logger):
    logger.info(f"Creating scout args")
    options = scour_args()
    
    options.enable_id_stripping = True
    options.shorten_ids = True        
    options.remove_metadata = True    
    options.strip_xml_prolog = True   
    options.strip_xml_space = True   

    return options

def optimize_svg(input_file, output_file, logger):
    logger.info(f"Setting up scour params")
    options = get_scour_params(logger)
    
    options.infilename = input_file
    options.outfilename = output_file
    
    logger.info(f"Setting scour_io in: {input_file} out: {output_file} ")
    (input_svg, output_svg) = scour_io(options)
    logger.info(f"Optimizing {input_svg} and saving it at {output_file}")
    scour(options, input_svg, output_svg)
    logger.info(f"Optimization was completed successfully")

def load_optimized_svg(input_file, task_dir, logger, scour=False):
    basename = os.path.basename(input_file)
    
    if scour:
        logger.info(f"Optimizing {input_file} with scour")
        load_file = os.path.join(task_dir, "scour", basename)
        optimize_svg(input_file, load_file, logger)
        logger.info(f"Optimized file saved into {load_file}")
    else:
        load_file = input_file

    logger.info(f"Parsing optimized File")
    tree = etree.parse(load_file)
    
    logger.info(f"Breaking polylines and polygons")
    path_tree = poly2path(tree, logger)
    logger.info(f"Breaking polylines and polygons finished")

    logger.info(f"Removing useless (zero lenght) paths")
    path_tree = remove_trivial_paths(path_tree, logger)

    return path_tree


def main():
    process()

if __name__ == "__main__":
    main()