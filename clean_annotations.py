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
        default="./dataset/test/test/svg_gt",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory for output results.",
        default="./clean_annotations",
    )
    
    args = parser.parse_args()
    return args

def remove_annotations(svg_file, out_folder):
    SYSTEM_PROMPT = "You are an AI assistant specialized in analyzing and organizing information from architectural floor plans." \
                    "You will be given a sequence of text labels extracted from a CAD floor plan. Your task is to determine whether each " \
                    "text is simply an annotation or if it represents the name of a room or building area (also referred to as an `ambient name`). " \
                    "Your response should only include the names of rooms or areas, written exactly as they appear in the input. If none of the texts " \
                    "in the sequence refer to ambient names, respond with: NONE."

    tree = etree.parse(svg_file)
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    text_groups = defaultdict(list)

    text_elements = tree.xpath('//svg:text', namespaces=ns)
    for text_elem in text_elements:
        # Find the closest <g> ancestor (parent) of the <text> element
        group = text_elem.xpath('ancestor::svg:g[1]', namespaces={'svg': 'http://www.w3.org/2000/svg'})
    
        # If a <g> group is found, use its 'id' attribute to group the <text> elements
        if group:
            group = group[0]  # Get the closest <g> ancestor
            group_id = id(group)
            text_groups[group_id].append(text_elem)
        
    for group_id, text_elems in text_groups.items():  
        texts = [elem.text.strip().upper() for elem in text_elems]
        user_prompt = ','.join(texts)

        print("Calling Builder API")
        
        res = requests.post(
        'http://localhost:11434/api/chat',json={
            "model": "openhermes",
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
        extracted_texts = res.json()["message"]["content"]
        extracted_texts = [ex.strip().upper() for ex in extracted_texts.split(",")]

        for i, og_text in enumerate(texts):
            if og_text not in extracted_texts:
                if not any([og_text in ext for ext in extracted_texts]):
                    parent = text_elems[i].getparent()
                    parent.remove(text_elems[i])
    
    tree.write(os.path.join(out_folder, os.path.basename(svg_file)))

def main():
    args = get_args()
    os.makedirs(args.input_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    svg_paths = glob.glob(os.path.join(args.input_dir,'*.svg'))
    
    for file in tqdm(svg_paths):
        print(f"File {file}")
        remove_annotations(file, args.output_dir)

if __name__ == "__main__":
    main()