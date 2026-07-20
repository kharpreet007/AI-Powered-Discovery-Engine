import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class CategoryMentioned(str, Enum):
    # Core
    FRUITS_VEGETABLES = "Fruits & Vegetables"
    DAIRY_BAKERY = "Dairy & Bakery"
    SNACKS_BEVERAGES = "Snacks & Beverages"
    STAPLES_GROCERY = "Staples/Grocery"
    PERSONAL_CARE_CLEANING = "Personal Care & Cleaning"

    # Exploratory
    ELECTRONICS = "Electronics & Accessories"
    BEAUTY_SKINCARE = "Beauty & Skincare"
    PHARMACY_HEALTH = "Pharmacy/Health"
    BABY_CARE = "Baby Care"
    PET_CARE = "Pet Care"
    STATIONERY_PRINT = "Stationery & Print"
    HOME_KITCHEN = "Home & Kitchen"
    BOOKS = "Books"

    # Catch-all
    OTHER = "other"
    NOT_STATED = "not stated"

class CategoryTier(str, Enum):
    CORE = "core"
    EXPLORATORY = "exploratory"
    NOT_STATED = "not stated"

class BehaviorType(str, Enum):
    REPEAT_PURCHASE = "repeat-purchase"
    FIRST_TIME_TRIAL = "first-time-trial"
    SWITCHED_FROM_COMPETITOR = "switched-from-competitor"
    ABANDONED_PURCHASE = "abandoned-purchase"
    STOCK_UP = "stock-up"
    IMPULSE_BUY = "impulse-buy"
    NOT_STATED = "not stated"

class DiscoveryChannel(str, Enum):
    APP_HOME_FEED = "app home feed"
    SEARCH_BAR = "search bar"
    PUSH_NOTIFICATION = "push notification"
    WORD_OF_MOUTH = "word of mouth"
    SOCIAL_MEDIA = "social media"
    EXTERNAL_AD = "external ad"
    NOT_STATED = "not stated"

class BarrierType(str, Enum):
    PRICE_TOO_HIGH = "price too high"
    TRUST_QUALITY = "trust/quality concerns"
    OUT_OF_STOCK = "out of stock"
    POOR_SELECTION = "poor selection"
    DELIVERY_ISSUES = "delivery issues (time/condition)"
    APP_UX_ISSUES = "app ux issues"
    NOT_STATED = "not stated"

class SegmentSignal(str, Enum):
    STUDENT = "student/bachelor"
    HOMEMAKER = "homemaker/family shopper"
    WORKING_PROFESSIONAL = "working professional (time-poor)"
    LATE_NIGHT_SHOPPER = "late night shopper"
    ELDERLY = "elderly/senior"
    NOT_STATED = "not stated"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class EvidenceType(str, Enum):
    DIRECT = "direct"
    PROXY = "proxy"

CATEGORY_KEYWORDS = {
    "Fruits & Vegetables": ["fruit", "vegetable", "veg", "tomato", "onion", "potato", "apple", "banana", "fresh"],
    "Dairy & Bakery": ["milk", "bread", "butter", "cheese", "paneer", "curd", "yogurt", "egg", "bakery"],
    "Snacks & Beverages": ["chips", "coke", "pepsi", "cold drink", "snack", "biscuit", "namkeen", "chocolate", "soda"],
    "Staples/Grocery": ["rice", "dal", "flour", "atta", "oil", "sugar", "salt", "spices", "masala"],
    "Personal Care & Cleaning": ["shampoo", "soap", "toothpaste", "detergent", "cleaner", "harpic", "surf excel"],
    "Electronics & Accessories": ["charger", "cable", "earphone", "power bank", "trimmer", "bulb", "battery"],
    "Beauty & Skincare": ["makeup", "cream", "lotion", "facewash", "lipstick", "perfume", "deodorant"],
    "Pharmacy/Health": ["condom", "medicine", "pill", "pad", "sanitary", "bandaid", "crocin", "health"],
    "Baby Care": ["diaper", "pampers", "baby food", "cerelac", "wipes"],
    "Pet Care": ["dog food", "cat food", "pedigree", "whiskas", "pet toy"],
    "Stationery & Print": ["pen", "notebook", "paper", "printout", "stapler", "tape"],
    "Home & Kitchen": ["cookware", "pan", "bottle", "container", "tissue", "foil", "garbage bag"],
    "Books": ["book", "novel", "magazine"]
}

BEHAVIOR_SIGNAL_WORDS = [
    "always buy", "first time", "switched from", "stopped using", 
    "stock up", "bulk", "craving", "midnight", "urgent", "forgot"
]

TECH_ONLY_VOCAB = [
    "app crash", "ui", "ux", "payment failed", "refund", "customer care", 
    "otp", "login issue", "location error"
]

SEED_QUESTIONS = [
    "Why do users repeatedly buy from the same categories?",
    "What prevents users from exploring new categories?",
    "How do users discover products today?",
    "What role do habits play in shopping behavior?",
    "What information do users need before trying a new category?",
    "What frustrations emerge repeatedly?",
    "Which user segments are more likely to experiment?",
    "What unmet needs emerge consistently across discussions?"
]

class Settings(BaseSettings):
    groq_api_key: str = ""
    gemini_api_key: str = ""
    youtube_api_key: str = ""
    admin_ingest_token: str = ""
    
    data_dir: str = "./data"
    chroma_dir: str = "./data/chroma_snapshot"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
