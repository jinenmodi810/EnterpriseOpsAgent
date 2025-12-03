from fastapi import APIRouter

router = APIRouter()

@router.post("/recommend")
def recommend():
    return {"message": "Recommend endpoint working"}