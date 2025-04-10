import os
from lxml import etree
import argparse
import requests
import glob
from tqdm import tqdm
from collections import defaultdict

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

def remove_annotations(tree, logger):
    SYSTEM_PROMPT =  "You're an AI floor plan assistant that receives texts present in a CAD blueprint and determine if they're the name of a room/ambient in a building or not. Room/Ambient name examples " \
                     "are rooms, restrooms, elevators, etc. Your answer will ONLY be 'YES' for rooms/ambients or 'NO' for the rest"
    
    MODEL = "mistral-openorca"

    ns = {'svg': 'http://www.w3.org/2000/svg'}

    text_paths = tree.xpath('//svg:text', namespaces=ns)
    text_elements = []
    for elem in text_paths:
        if elem.text:
            text_elements.append(elem)
        else:
            tspans = [tspan for tspan in elem.xpath('.//svg:tspan', namespaces=ns) if tspan.text]
            text_elements.extend(tspans)

    to_remove = []
    for elem in text_elements:
        if elem.text:
            try:
                user_prompt = elem.text.upper()
            except:
                elem = [tspan for tspan in elem.xpath('.//svg:tspan', namespaces=ns) if tspan.text]
                user_prompt = elem.text
            logger.info(f"Processing text {user_prompt}") 
            logger.info("Calling Builder API")
            
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
            logger.info("API Called successfully")
            is_room = res.json()["message"]["content"].strip().upper()
            logger.info(f"AI AUTOMATED: Is room? {is_room}")
            if is_room == "NO":
                to_remove.append(elem)
                logger.info(f"Element Removed")
    

    for elem in to_remove:
        parent = elem.getparent()
        if parent:
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