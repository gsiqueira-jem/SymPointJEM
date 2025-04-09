from scour.scour import start as scour, parse_args as scour_args, getInOut as scour_io
from io import BytesIO
from lxml import etree
import os
import glob
import argparse
from tqdm import tqdm
from math import hypot


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

def is_trivial_path(d_attr, tolerance=0.0):
    try:
        tokens = d_attr.strip().split()
        if len(tokens) != 6 or tokens[0] != 'M' or tokens[3] != 'L':
            return False
        x1, y1 = float(tokens[1]), float(tokens[2])
        x2, y2 = float(tokens[4]), float(tokens[5])
        return hypot(x2 - x1, y2 - y1) <= tolerance
    except:
        return False


def poly2path(tree):
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
    
    print(f"{no_info} polylines/polygons skipped because of no info")
    print(f"{trivial} polylines/polygons skipped because of being 0 length")

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

def load_optimized_svg(input_file, task_dir, logger):
    basename = os.path.basename(input_file)
    output_file = os.path.join(task_dir, "scour", basename)
    
    # logger.info(f"Optimizing {input_file} with scour")
    # optimize_svg(input_file, output_file, logger)
    # logger.info(f"Optimized file saved into {output_file}")
    
    logger.info(f"Parsing optimized File")
    tree = etree.parse(input_file)
    
    logger.info(f"Breaking polylines and polygons")
    path_tree = poly2path(tree)
    logger.info(f"Breaking polylines and polygons finished")
    
    return path_tree


def main():
    process()

if __name__ == "__main__":
    main()