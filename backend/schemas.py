from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MealCreate(BaseModel):
    """Schema for creating a meal entry with nutrition data"""
    meal_name: str = "Manual Entry"
    
    # All nutrient fields - Optional with None default
    Caloric_Value: Optional[float] = None
    Carbohydrates: Optional[float] = None
    Fat:  Optional[float] = None 
    Saturated_Fat:Optional[float] = None
    Monounsaturated_Fat:Optional[float] = None
    Polyunsaturated_Fat: Optional[float] = None
    Sugars: Optional[float] = None
    Protein: Optional[float] = None
    Dietary_Fiber: Optional[float] = None
    Cholesterol: Optional[float] = None
    Sodium: Optional[float] = None
    Water: Optional[float] = None
    Vitamin_A: Optional[float] = None
    Vitamin_B1: Optional[float] = None
    Vitamin_B11: Optional[float] = None
    Vitamin_B12: Optional[float] = None
    Vitamin_B2: Optional[float] = None
    Vitamin_B3: Optional[float] = None
    Vitamin_B5: Optional[float] = None
    Vitamin_B6: Optional[float] = None
    Vitamin_C: Optional[float] = None
    Vitamin_D: Optional[float] = None
    Vitamin_E: Optional[float] = None
    Vitamin_K: Optional[float] = None
    Calcium: Optional[float] = None
    Copper: Optional[float] = None
    Iron: Optional[float] = None
    Magnesium: Optional[float] = None
    Manganese: Optional[float] = None
    Phosporus: Optional[float] = None
    Selenium: Optional[float] = None
    Zinc: Optional[float] = None


class MealOut(BaseModel):
    """Schema for meal response including prediction and metadata"""
    id: int
    user_id: Optional[int] = None
    meal_name: str
    
    # All nutrient fields
    Caloric_Value: float
    Carbohydrates: float
    Sugars: float
    Protein: float
    Dietary_Fiber: float
    Cholesterol: float
    Sodium: float
    Water: float
    Vitamin_A: float
    Vitamin_B1: float
    Vitamin_B11: float
    Vitamin_B12: float
    Vitamin_B2: float
    Vitamin_B3: float
    Vitamin_B5: float
    Vitamin_B6: float
    Vitamin_C: float
    Vitamin_D: float
    Vitamin_E: float
    Vitamin_K: float
    Calcium: float
    Copper: float
    Iron: float
    Magnesium: float
    Manganese: float
    Phosporus: float
    Selenium: float
    Zinc: float
    
    # Prediction result and timestamp
    prediction: float
    created_at: datetime
    
    class Config:
        from_attributes = True  # For Pydantic v2 (was orm_mode = True in v1)


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"