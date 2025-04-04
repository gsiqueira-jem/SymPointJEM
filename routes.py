from fastapi import APIRouter, File, UploadFile
#from services.svg_loader import load_svg
#from services.svg_transformer import transform_svg
#from services.svg_writer import serialize_svg

router = APIRouter()

@router.post("/process-svg/")
async def process_svg(file: UploadFile = File(...)):
    contents = await file.read()
#    
#    root = load_svg(contents)
#    transformed = transform_svg(root)
#    modified_svg = serialize_svg(transformed)

#    return {"modified_svg": modified_svg}

    pass
