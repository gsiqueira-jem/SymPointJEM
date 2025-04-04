RAW_DIR="./dataset/test/test/raw"
PROCESSED_DIR="./dataset/test/test/svg_gt" 
PYTHON_SCRIPT="preprocess_svg.py"

for file in "$RAW_DIR"/*.svg; do
    filename=$(basename "$file")
    processed_file="$PROCESSED_DIR/$filename"

    echo "Optimizing: $file into $processed_file"
    scour -i "$file" --enable-id-stripping --shorten-ids --remove-metadata --strip-xml-prolog --strip-xml-space "$processed_file" 
done

echo "Regularizing polylines and polygons for files:"
python3 "$PYTHON_SCRIPT" --input_dir "$PROCESSED_DIR" --output_dir "$PROCESSED_DIR"