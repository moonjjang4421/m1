from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.database import Repository
from backend.dependencies import get_repository
from backend.models import DataCreate, DataRecord, DataUpdate
from backend.services.summary import build_summary

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/summary")
def read_summary(repo: Repository = Depends(get_repository)) -> dict:
    return build_summary(repo.list_data())


@router.post("", response_model=DataRecord, status_code=status.HTTP_201_CREATED)
def create_data(payload: DataCreate, repo: Repository = Depends(get_repository)) -> dict:
    return repo.create_data(payload.model_dump(mode="json"))


@router.get("", response_model=list[DataRecord])
def list_data(repo: Repository = Depends(get_repository)) -> list[dict]:
    return repo.list_data()


@router.put("/{record_id}", response_model=DataRecord)
def update_data(record_id: str, payload: DataUpdate, repo: Repository = Depends(get_repository)) -> dict:
    changes = payload.model_dump(mode="json", exclude_none=True)
    if not changes:
        raise HTTPException(status_code=422, detail="수정할 값을 하나 이상 입력하세요.")
    record = repo.update_data(record_id, changes)
    if not record:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data(record_id: str, repo: Repository = Depends(get_repository)) -> Response:
    if not repo.delete_data(record_id):
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

