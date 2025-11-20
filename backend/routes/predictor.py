from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import joblib
import numpy as np
from datetime import datetime
from typing import List, Optional
from backend.schemas import MealCreate, MealOut
from backend.database import get_db, MealHistory, User
from backend.utils.jwt_handler import verify_token
import easyocr
import torch
from transformers import pipeline
from fastapi import UploadFile, File
import ast
# Initialize pipeline once (reuse for all labels)
pipe = pipeline(
    task="text-generation",
    model="HuggingFaceTB/SmolLM3-3B",

)
router = APIRouter(tags=["Prediction"])

# Load model

model = joblib.load("backend/routes/xgboost_model.joblib")


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
        "Caloric_Value","Fat","Saturated_Fat","Monounsaturated_Fat","Polyunsaturated_Fat", "Carbohydrates", "Sugars", "Protein", "Dietary_Fiber", "Cholesterol",
        "Sodium", "Water", "Vitamin_A", "Vitamin_B1", "Vitamin_B11", "Vitamin_B12",
        "Vitamin_B2", "Vitamin_B3", "Vitamin_B5", "Vitamin_B6", "Vitamin_C", "Vitamin_D",
        "Vitamin_E", "Vitamin_K", "Calcium", "Copper", "Iron", "Magnesium", "Manganese","Potassium",
        "Phosporus", "Selenium", "Zinc"
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

@router.post("/img_to_text")
async def img_to_text(image: UploadFile = File(...), 
    Authorization: Optional[str] = Header(None)):
    contents = await image.read()
    reader = easyocr.Reader(['en'])
    result = reader.readtext(contents, detail=0)
    # Combine all detected text into a single string
    hypothesis = ' '.join(result)
    nutritional_content=nutrient_extractor(hypothesis)
    nutritional_quantity=helper(nutritional_content)
    return nutritional_quantity


def nutrient_extractor(ocr_text):
    messages = [
        {
            "role": "system",
            "content": """/no_think
You are a nutrient extraction assistant. Extract nutritional information from food labels and map to standard nutrient names.

Standard nutrients: Caloric_Value, Carbohydrates, Sugars, Protein, Dietary_Fiber, Cholesterol, Sodium, Water, Vitamin_A, Vitamin_B1, Vitamin_B11, Vitamin_B12, Vitamin_B2, Vitamin_B3, Vitamin_B5, Vitamin_B6, Vitamin_C, Vitamin_D, Vitamin_E, Vitamin_K, Calcium, Copper, Iron, Magnesium, Manganese, Phosporus, Selenium, Zinc, Fats, trans_fat

Return as Python list of tuples: [("nutrient_name", "value")]"""
        },
        # Few-shot examples
        {
            "role": "user",
            "content": "Extract from: Nutrition Facts Serving Size: 2 tbsp (32g) Calories 80 Total Fat 7g Saturated Fat 1g Trans Fat 0g Cholesterol 0mg Sodium 80mg Total Carbohydrate 4g Dietary Fiber 1g Sugars 2g Protein 2g Vitamin D 0mcg Calcium 10mg Iron 0.3mg Potassium 90mg"
        },
        {
            "role": "assistant",
            "content": '[("Caloric_Value", "80"), ("Fats", "7"), ("Saturated_Fat", "1"), ("trans_fat", "0"), ("Cholesterol", "0"), ("Sodium", "80"), ("Carbohydrates", "4"), ("Dietary_Fiber", "1"), ("Sugars", "2"), ("Protein", "2"), ("Vitamin_D", "0"), ("Calcium", "10"), ("Iron", "0.3"), ("Potassium", "90")]'

        },
        {
            "role": "user",
            "content": "Extract from: Nutrition Facts Serving Size 1 oz (28g/about 25 chips) Servings Per Container 7 Amount Per Serving Calories 140 Calories from Fat 90% Daily Value* Total Fat 10g 15% Saturated Fat 1g 5% Trans Fat 0g Cholesterol 0mg 0% Sodium 100mg 4% Total Carbohydrate 13g 4% Dietary Fiber less than 1g 4% Sugars 1g Protein 2g Vitamin A 2% Vitamin C 6% Calcium 0% Iron 4%"
        },
        {
            "role": "assistant",
            "content": '[("Caloric_Value", "140"),("Fats", "10"),("Saturated_Fat", "1"),("trans_fat", "0"),("Cholesterol", "0"),("Sodium", "100"),("Carbohydrates", "13"),("Dietary_Fiber", "0.9"),("Sugars", "1"),("Protein", "2"),("Vitamin_A", "2"),("Vitamin_C", "6"),("Calcium", "0"),("Iron", "4")]'
        },

        # Actual query
        {
            "role": "user",
            "content": f"Extract from: {ocr_text}"
        }
    ]
    

    # Generate with pipeline
    outputs = pipe(
        messages,

        do_sample=True,
        temperature=0.1,  # Low temp for consistent output
        top_p=0.95
    )

    # Extract the assistant's response
    result = outputs[0]["generated_text"][-1]["content"].strip()
    extracted = ast.literal_eval(result)
    
    return extracted
    
# Output: [("Caloric_Value", "300 kcal"), ("Protein", "12 g"), ("Cholesterol", "5 mg"), ("Fats", "8 g")]


def helper(output_list):
    result = {}
    for nutrient_name, value_str in output_list:
        try:
            result[nutrient_name] = float(value_str)  # keep as float, not int!
        except:
            result[nutrient_name] = 0.0
    return result