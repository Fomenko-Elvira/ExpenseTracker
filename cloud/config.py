import os

DATABASE_URL = "https://expensetracker-844bc-default-rtdb.europe-west1.firebasedatabase.app"

API_KEY = "AIzaSyBVE_YitUtF2dhgDglQy0uaziOZL0hkl34"

FIREBASE_EMAIL = os.environ.get("FIREBASE_EMAIL", "")
FIREBASE_PASSWORD = os.environ.get("FIREBASE_PASSWORD", "")

TIMEOUT = 15