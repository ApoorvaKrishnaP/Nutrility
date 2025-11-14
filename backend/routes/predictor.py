from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import joblib
import numpy as np
from datetime import datetime
from typing import List, Optional

from backend.schemas import MealCreate, MealOut
from backend.database import get_db, MealHistory, User
from backend.utils.jwt_handler import verify_token

router = APIRouter(tags=["Prediction"])

# Load model
try:
    model = joblib.load("backend/routes/linear_regression_model.pkl")
except FileNotFoundError:
    try:
        model = joblib.load("backend\\routes\\linear_regression_model.pkl")
    except FileNotFoundError:
        raise RuntimeError("Model file not found. Please ensure linear_regression_model.pkl exists in backend/routes/")

@router.post("/predict", response_model=MealOut)
def predict_meal(meal: MealCreate, Authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Predict nutrition density score for a meal.
    Accepts all nutrient fields, defaults missing values to 0.
    """
    # Optional auth: if provided, validate and find user
    user = None
    if Authorization:
        parts = Authorization.split(" ")
        if len(parts) == 2:
            token = parts[1]
            username = verify_token(token)
            if not username:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            user = db.query(User).filter(User.username == username).one_or_none()

    # Build feature vector - ensure all 28 features are present
    feature_names = [
        "Caloric_Value", "Carbohydrates", "Sugars", "Protein", "Dietary_Fiber", "Cholesterol",
        "Sodium", "Water", "Vitamin_A", "Vitamin_B1", "Vitamin_B11", "Vitamin_B12",
        "Vitamin_B2", "Vitamin_B3", "Vitamin_B5", "Vitamin_B6", "Vitamin_C", "Vitamin_D",
        "Vitamin_E", "Vitamin_K", "Calcium", "Copper", "Iron", "Magnesium", "Manganese",
        "Phosporus", "Selenium", "Zinc",
    ]

    # Extract values, defaulting to 0.0 for any missing fields
    vals = []
    for name in feature_names:
        value = getattr(meal, name, None)
        if value is None:
            value = 0.0
        vals.append(float(value))
    
    features = np.array([vals], dtype=float)

    # Predict nutrition density score
    try:
        prediction = float(model.predict(features)[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {e}")

    # Save to database
    meal_entry = MealHistory(
        user_id=user.id if user else None,
        meal_name=meal.meal_name,
        Caloric_Value=meal.Caloric_Value or 0.0,
        Carbohydrates=meal.Carbohydrates or 0.0,
        Sugars=meal.Sugars or 0.0,
        Protein=meal.Protein or 0.0,
        Dietary_Fiber=meal.Dietary_Fiber or 0.0,
        Cholesterol=meal.Cholesterol or 0.0,
        Sodium=meal.Sodium or 0.0,
        Water=meal.Water or 0.0,
        Vitamin_A=meal.Vitamin_A or 0.0,
        Vitamin_B1=meal.Vitamin_B1 or 0.0,
        Vitamin_B11=meal.Vitamin_B11 or 0.0,
        Vitamin_B12=meal.Vitamin_B12 or 0.0,
        Vitamin_B2=meal.Vitamin_B2 or 0.0,
        Vitamin_B3=meal.Vitamin_B3 or 0.0,
        Vitamin_B5=meal.Vitamin_B5 or 0.0,
        Vitamin_B6=meal.Vitamin_B6 or 0.0,
        Vitamin_C=meal.Vitamin_C or 0.0,
        Vitamin_D=meal.Vitamin_D or 0.0,
        Vitamin_E=meal.Vitamin_E or 0.0,
        Vitamin_K=meal.Vitamin_K or 0.0,
        Calcium=meal.Calcium or 0.0,
        Copper=meal.Copper or 0.0,
        Iron=meal.Iron or 0.0,
        Magnesium=meal.Magnesium or 0.0,
        Manganese=meal.Manganese or 0.0,
        Phosporus=meal.Phosporus or 0.0,
        Selenium=meal.Selenium or 0.0,
        Zinc=meal.Zinc or 0.0,
        prediction=prediction,
        created_at=datetime.utcnow(),
    )

    db.add(meal_entry)
    db.commit()
    db.refresh(meal_entry)

    # Return the complete meal entry with prediction
    return meal_entry


@router.get("/meals", response_model=List[MealOut])
def get_meals(Authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Get meal history.
    If authenticated, returns meals for that user.
    Otherwise returns empty list or recent public meals.
    """
    user = None
    if Authorization:
        parts = Authorization.split(" ")
        if len(parts) == 2:
            token = parts[1]
            username = verify_token(token)
            if username:
                user = db.query(User).filter(User.username == username).one_or_none()

    if user:
        # Return meals for authenticated user, ordered by newest first
        meals = (
            db.query(MealHistory)
            .filter(MealHistory.user_id == user.id)
            .all()
        )
    
    
    return meals