from fastapi import APIRouter

router = APIRouter()

@router.post("/predict")
def predict():
    return {"message": "Predict endpoint working"}