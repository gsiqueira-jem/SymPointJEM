import os
from tqdm import tqdm
from xml.etree import ElementTree as ET

# Define the semantic ID groups
NON_STRUCTURE_IDS = {-1, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 31, 32, 35, 36}
STRUCTURE_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 28, 29, 30, 33, 34}

def update_semantic_ids_in_svg(file_path, output_dir):
    tree = ET.parse(file_path)
    root = tree.getroot()

    for elem in root.iter():
        if "semanticId" in elem.attrib:
            try:
                val = int(elem.attrib["semanticId"])
                if val in NON_STRUCTURE_IDS:
                    elem.attrib["semanticId"] = "0"
                elif val in STRUCTURE_IDS:
                    elem.attrib["semanticId"] = "1"
            except ValueError:
                continue  # Ignore non-integer semanticId values

    filename = os.path.basename(file_path)
    output_path = os.path.join(output_dir, filename)
    tree.write(output_path)

def process_directory(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for file_name in tqdm(os.listdir(input_dir)):
        if file_name.lower().endswith(".svg"):
            file_path = os.path.join(input_dir, file_name)
            update_semantic_ids_in_svg(file_path, output_dir)

def main():
    splits = ["train", "val", "test"]
    for split in splits:
        print(f"Processing {split} split")
        input_path=f"./dataset/{split}/{split}/svg_gt/"
        output_path=f"./dataset/{split}/{split}/binarized/"
        process_directory(input_path, output_path)

if __name__ == "__main__":
    main()