from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from sqlalchemy import  Column, String, Integer, create_engine,
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException

app = FastAPI()

# PostgreSQL database
SQLALCHEMY_DATABASE_URL = "postgresql://admin:1234@localhost/test1"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB
MONGO_DB = "demo1"
MONGO_URI = "mongodb://localhost:27017/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
profile_picture_collection = mongo_db["profile_pictures"]


# PostgreSQL table
class UserPostgreSQL(Base):
    __tablename__ = "users"
    User_id = Column(Integer, primary_key=True)
    first_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)


class UserRegistrationRequest(BaseModel):
    user_id:int
    first_name: str
    email: EmailStr
    password: str
    phone: str
    profile_picture_url: str


# Creating user registration
@app.post("/register/")
def register_user(user_req: UserRegistrationRequest):
    db = SessionLocal()
    email_exist = db.query(UserPostgreSQL).filter_by(email=user_req.email).first()
    if email_exist:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = UserPostgreSQL(
        user_id = user_req.user_id,
        first_name=user_req.first_name,
        email=user_req.email,
        password=user_req.password,
        phone=user_req.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    # calling profile picture upload
    upload_profile_picture(user_req.user_id,user_req.profile_picture_url)

    return new_user


# Getting user details by user_id
@app.get("/user/{user_id}/")
def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(UserPostgreSQL).filter_by(user_id=user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# uploading profile picture to MongoDB using without SQLALCHEMY
def upload_profile_picture(user_id: int, image_url: str):
    profile_picture_collection.insert_one({"user_id": user_id, "image_url": image_url})
    return {"message": "Profile picture uploaded successfully"}
