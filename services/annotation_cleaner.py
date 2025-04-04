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

def remove_annotations(tree):
    SYSTEM_PROMPT =  "You're an AI CAD assistant that extract room or building ambient names from a sequence "\
    "of text entries, separated by SEMICOLON. Building ambient names are such as: Janitors Closet, Men's Restroom" \
    "Lobby, etc.. The AI Assistant should follow the following rules:"
    "\n\n"
    "- Combine tokens when they form a complete room name (e.g. 'FIRE; COMMAND; ROOM' -> 'FIRE COMMAND ROOM').\n"\
    "- Keep the room name exactly as it appears in the original input. (e.g. 'MEN'S RSTRM' -> 'MEN'S RSTRM')\n"\
    "- Return only the room names found in the input, in the order they appear.\n"\
    "- If no ambient name is found the response will be 'NONE'.\n"
    "- Your response will either be 'NONE' or the extracted sequence, nothing else, no more text"
    "\n\n"\
    "Example #1:\n"\
    "User: FIRE; COMMAND; ROOM; 2CM; 2X10; GRAND LOBBY; SEE PLANS; ELEV #1\n"\
    "Assistant: FIRE COMMAND ROOM; GRAND LOBBY; ELEV #1\n"\
    "Example #2:\n"\
    "User: L1-02;3'-4\";P1-08\n"\
    "Assistant: NONE\n"\
    
    MODEL = "mistral-openorca"

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
    
    text_groups = merge_short_lists(text_groups, 7)
    
    for group_id, text_elems in tqdm(text_groups.items()):  
        texts = [elem.text.strip().upper() for elem in text_elems]
        user_prompt = ';'.join(texts)

        print("Calling Builder API")
        print(f"Input: {user_prompt}")
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
        extracted_texts = res.json()["message"]["content"]
        print(f"Network output: {extracted_texts}")
        extracted_texts = [ex.strip().upper() for ex in extracted_texts.split(",")]

        for i, og_text in enumerate(texts):
            if og_text not in extracted_texts:
                if not any([og_text in ext for ext in extracted_texts]):
                    parent = text_elems[i].getparent()
                    parent.remove(text_elems[i])
    
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