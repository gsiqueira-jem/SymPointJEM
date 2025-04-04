from services.svg_loader import load_optimized_svg
from services.annotation_cleaner import remove_annotations
from services.json_parser import parse_svg



def main():
    test_file = "./dataset/test/test/raw/1-Crosby_Original_Model.svg"

    optimized_tree = load_optimized_svg(test_file)
    no_annotations_tree = remove_annotations(optimized_tree)
    json_repr = parse_svg(no_annotations_tree)

    print(json_repr)
    print(no_annotations_tree)



if __name__ == "__main__":
    main()