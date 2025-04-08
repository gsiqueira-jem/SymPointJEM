import os
from fastapi import APIRouter, File, UploadFile, Form
from threading import Thread
from uuid import uuid4
from test_workflow import cad_workflow
#from services.svg_loader import load_svg
#from services.svg_transformer import transform_svg
#from services.svg_writer import serialize_svg

router = APIRouter()
task_status = {}

async def process_cad(task_id, file, filename):
    task_status[task_id] = {"status" : "running", "result_path" : None}
    FILE_LOC = f"/tmp/{task_id}"

    os.makedirs(FILE_LOC, exist_ok=True)
    file_path = os.path.join(FILE_LOC, filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    output_file = cad_workflow(file_path)
    
    task_status[task_id]["status"] = "done"
    task_status[task_id]["file_path"] = output_file

@router.get("/cad-cleaner")
def cad_ok():
    return {"message" : "CadCleaner is running on port 8000"}

@router.post("/cad-cleaner/process-svg/")
async def process_svg(file: UploadFile = File(...), filename: str = Form(...)):
    task_id = str(uuid4())
    
    thread = Thread(target=process_cad,args=(task_id, file, filename))
    thread.start()
    
    return { "task_id": task_id }

@router.get("/cad-cleaner/task-status/{task_id}")
def get_status(task_id: str):
    status = task_status.get(task_id)
    if status is None:
        return {"status": "not_found"}
    
    return status