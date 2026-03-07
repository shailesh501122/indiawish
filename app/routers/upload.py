import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

# Construct the path to local uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    Accepts multiple image files and saves them to the local `uploads` directory.
    Returns a list of URLs that can be used to display the images.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    uploaded_urls = []
    for file in files:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' is not an image.")
        
        # Generate a unique filename to prevent collisions
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # The URL path relative to the domain
            # We will mount the static directory at /uploads in main.py
            uploaded_urls.append(f"/uploads/{unique_filename}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload '{file.filename}': {str(e)}")
            
    return {"urls": uploaded_urls}
