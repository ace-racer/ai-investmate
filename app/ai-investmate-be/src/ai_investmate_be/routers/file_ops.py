import os
import shutil
from tempfile import NamedTemporaryFile
from typing import Annotated, List

from ai_investmate_be.constants import EMBEDDING_MODEL_DIMENSION
from ai_investmate_be.file_processor import process_uploaded_file
from ai_investmate_be.models import FileDetails
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pinecone import Pinecone

router = APIRouter()


@router.post("/upload/")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()],
):
    file_size = file.size
    if file_size > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size too large. Max size is 5 MB.")
    print(f"file_size: {file_size} bytes")
    print(f"file_name: {file.filename}")
    file_details = {
        "name": name,
        "description": description,
        "file_name": file.filename,
    }
    print(f"file_details: {file_details}")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    result = index.query(
        vector=[0] * EMBEDDING_MODEL_DIMENSION,
        filter={"name": {"$eq": name}},
        top_k=10,
        include_values=True,
    )
    # {"$and": [{"genre": "comedy"}, {"genre":"documentary"}]}
    # result = index.query(vector=[0] * EMBEDDING_MODEL_DIMENSION, filter={"$or": [{"name": { "$eq": name } }, {"file_name": { "$eq": file.filename } }]}, top_k=10, include_values=True)
    if len(result.matches) > 0:
        print(f"Files with name {name} already exists, so not adding again")
        return {"message": f"Files with name {name} already exists, so not adding again..."}

    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        downloaded_file_path = temp_file.name
        # Pass the file path/object path to a worker to further process the file
        background_tasks.add_task(
            process_uploaded_file, file.filename, downloaded_file_path, file_details
        )
    print(f"File {name} is being processed now...")
    return {"message": f"File {name} is being processed now..."}


@router.post("/files/")
async def get_files() -> List[FileDetails]:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    index.query(filter={"name": {"$eq": "name"}}, top_k=500, include_values=True)


@router.delete("/remove/{name}")
async def delete_file(name: str) -> int:
    if name.strip():
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
        docs_deleted = 0
        while True:
            # Need to pass the vector as all 0's as just metadata won't work (weird)
            # https://community.pinecone.io/t/weird-error-when-running-index-query/3699/2
            result = index.query(
                vector=[0] * EMBEDDING_MODEL_DIMENSION,
                filter={"name": {"$eq": name}},
                top_k=1000,
                include_values=True,
            )
            if len(result.matches) > 0:
                match_ids = [m.id for m in result.matches]
                print(f"match_ids for name: {name}: {match_ids}")
                index.delete(ids=match_ids)
                docs_deleted += len(result.matches)
            else:
                print("No more records to delete...")
                break

        return docs_deleted
    return 0
