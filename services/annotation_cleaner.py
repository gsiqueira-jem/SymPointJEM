import os
from lxml import etree
import argparse
import requests
import glob
import math
from tqdm import tqdm
from collections import defaultdict
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
        default="../dataset/test/test/svg_gt",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory for output results.",
        default="../clean_annotations",
    )
    
    args = parser.parse_args()
    return args

def merge_short_lists(d, threshold):
    keys = list(d.keys())
    new_dict = {}
    i = 0

    while i < len(keys):
        current_key = keys[i]
        current_list = d[current_key]

        # If current list meets the threshold, add it as is
        if len(current_list) >= threshold:
            new_dict[current_key] = current_list
            i += 1
        else:
            # Merge with next lists until threshold is met or no more lists
            combined = current_list[:]
            j = i + 1
            while len(combined) < threshold and j < len(keys):
                combined += d[keys[j]]
                j += 1
            new_key = f"{current_key}_to_{keys[j-1]}" if j-1 != i else current_key
            new_dict[new_key] = combined
            i = j  # Skip over merged lists

    return new_dict

def is_room(user_prompt, logger):
    SYSTEM_PROMPT = (
        "You are an AI floor plan assistant. You receive texts found in a CAD blueprint and must determine whether "
        "each text is the name of a room or ambient (like rooms, restrooms, elevators, etc.), "
        "or if it is an annotation.\n"
        "Respond ONLY with 'YES' for room/ambient names, and 'NO' for everything else.\n"
        "If the text contains both a room name and an annotation, respond with 'NO'. Only texts that clearly and solely "
        "name a room/ambient should receive 'YES'.\n\n"
        "Examples:\n"
        "user: \"1250 SQRFT GENERATOR ROOM\"\n"
        "assistant: \"NO\"\n\n"
        "user: \"GENERATOR ROOM\"\n"
        "assistant: \"YES\"\n\n"
        "user: \"ST1-01\"\n\n"
        "assistant: \"NO\"\n\n"
    )


    MODEL = "llama3"
    logger.info(f"Calling CAD Assistant for {user_prompt}")
    res = requests.post(
            'http://10.11.0.50:11434/api/chat',json={
                "model": MODEL,
                "messages": [
                    { 
                        "role": "system", 
                        "content": SYSTEM_PROMPT
                    },

                    { 
                        "role": "user", 
                        "content": user_prompt
                    }
                ],
                "stream" : False
            })
    is_room = res.json()["message"]["content"].strip().upper()
    logger.info(f"Is {user_prompt} a room ? {is_room}")
    return is_room == "YES"


def extract_info(elem):
    transform = elem.attrib.get('transform', '')
    font_size = float(elem.attrib.get('font-size', '1'))
    matrix_re = re.compile(r'matrix\(([^)]+)\)')
    match = matrix_re.search(transform)
    if not match:
        return None
    a, b, c, d, e, f = map(float, match.group(1).split())
    return {
        'elem': elem,
        'x': e,
        'y': f,
        'font_size_x': a * font_size,
        'font_size_y': d * font_size
    }

def is_close(e1, e2):
    x_tolerance = 5.0
    y_tolerance = 2.0

    dx = abs(e1['x'] - e2['x'])
    dy = abs(e1['y'] - e2['y'])
    return (
        dx < e1['font_size_x'] * x_tolerance and
        dy < e1['font_size_y'] * y_tolerance
    )



def should_group(t1, t2):
    categories = ["font-family", "fill", "font-size", "style"]
     
    for c in categories:
        if t1.attrib.get(c) and t2.attrib.get(c):
            if t1.attrib[c] != t2.attrib[c]:
                return False
    et1, et2 = extract_info(t1), extract_info(t2)
    return is_close(et1, et2)
        
def create_groups(text_elements):
    current_group = []
    groups = []

    for elem in text_elements:
        if not current_group:
            current_group.append(elem)
        else:
            prev = current_group[-1]
            if should_group(prev, elem):
                current_group.append(elem)
            else:
                groups.append(current_group)
                current_group = [elem]
    if current_group:
        groups.append(current_group)
    
    return groups


def get_room_mask(text_seq, logger):
    count = len(text_seq)
    best_range = None
    best_len = 0

    for start in range(count):
        for end in range(start + 1, count + 1):
            subseq = " ".join(text_seq[start:end])
            if is_room(subseq, logger):
                seq_len = end - start
                if not best_range or seq_len > best_len:
                    best_range = (start, end)
                    best_len = end - start
    
    if best_range:
        start, end = best_range
        return [start <= i < end for i in range(count)]
    else:
        return [False] * count

def get_text_from_elements(elements, ns):
    text_seq = []
    for elem in elements:
        if elem.text:
            text_seq.append(elem.text)
        else:
            tspan = [tspan for tspan in elem.xpath('.//svg:tspan', namespaces=ns) if tspan.text][0]
            text_seq.append(tspan.text)
    
    return text_seq

def remove_annotations(tree, logger):
    
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    text_paths = tree.xpath('//svg:text', namespaces=ns)
    text_groups = create_groups(text_paths)

    to_remove = []
    for group in text_groups:
        elements = [elem for elem in group]
        text_seq = get_text_from_elements(elements, ns)
        room_mask = get_room_mask(text_seq, logger)
        not_room = [el for el, keep in zip(elements, room_mask) if not keep]
        to_remove.extend(not_room)

    

    for elem in to_remove:
        parent = elem.getparent()
        if parent:
            logger.info(f"Element of text {elem.text} removed")
            parent.remove(elem)
    return tree

def load_remove_annotations(svg_file, out_folder):
    tree = etree.parse(svg_file)
    tree = remove_annotations(tree)
    tree.write(os.path.join(out_folder, os.path.basename(svg_file)))

def main():
    args = get_args()
    os.makedirs(args.input_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    svg_paths = glob.glob(os.path.join(args.input_dir,'*.svg'))
    
    for file in tqdm(svg_paths):
        print(f"File {file}")
        load_remove_annotations(file, args.output_dir)

if __name__ == "__main__":
    main()