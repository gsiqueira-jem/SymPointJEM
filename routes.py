import os
import logging
from fastapi import APIRouter, File, UploadFile, Form
from threading import Thread
from uuid import uuid4
from test_workflow import cad_workflow
import traceback

router = APIRouter()
task_status = {}


def setup_logger(task_id, log_folder):
    logger = logging.getLogger(task_id)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(os.path.join(log_folder, f"task_{task_id}.log"))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def create_dirs(task_id):
    TASK_PATH = f"/tmp/tasks/{task_id}"
    os.makedirs(TASK_PATH, exist_ok=True)
    
    LOGGING_LOC = os.path.join(TASK_PATH, "log")
    os.makedirs(LOGGING_LOC, exist_ok=True)
    FILE_LOC = os.path.join(TASK_PATH, "svg")
    os.makedirs(FILE_LOC, exist_ok=True)

    return TASK_PATH, FILE_LOC, LOGGING_LOC

def process_cad(task_id, content, filename):
    task_status[task_id] = {"status" : "running", "result_path" : None}
    TASK_DIR, FILE_LOC, LOGGING_LOC = create_dirs(task_id)
    
    file_path = os.path.join(FILE_LOC, filename)

    logger = setup_logger(task_id, LOGGING_LOC)
    logger.info(f"Task {task_id} created")

    try:
        logger.info("Starting task")
        with open(file_path, "wb") as f:
            f.write(content)
        
        output_file = cad_workflow(file_path, TASK_DIR, logger)

        task_status[task_id]["status"] = "done"
        task_status[task_id]["result_path"] = output_file

    except Exception as e:
        error_msg = f"Task {task_id} failed with error {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        task_status[task_id] = {"status": "error", "result_path": None}

@router.get("/cad-cleaner")
def cad_ok():
    return {"message" : "CadCleaner is running on port 8000"}

@router.post("/cad-cleaner/process-svg/")
async def process_svg(file: UploadFile = File(...), filename: str = Form(...)):
    task_id = str(uuid4())
    content = await file.read()

    thread = Thread(target=process_cad,args=(task_id, content, filename))
    thread.start()
    
    return { "task_id": task_id }

@router.get("/cad-cleaner/task-status/{task_id}")
def get_status(task_id: str):
    status = task_status.get(task_id)
    if status is None:
        return {"status": "not_found"}
    
    return status