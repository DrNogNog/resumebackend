# app/models/user_model.py
from sqlalchemy import Boolean, Column, Integer, String, Enum, JSON, DateTime, ForeignKey, Text
import enum
from app.core.sync_database import Base 
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy.sql import func, text

class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(Text)
    file = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PlanEnum(str, enum.Enum):
    free = "free"
    pro = "pro"
    pro_plus = "pro_plus"

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=False, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    # Auth fields
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_password_token = Column(String, nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
    refresh_token_hash = Column(String, nullable=True)
    refresh_token_expires = Column(DateTime, nullable=True)

    api_calls     = Column(Integer, nullable=False, server_default=text("2"))
    api_downloads = Column(Integer, nullable=False, server_default=text("1"))
    llm_runs      = Column(Integer, nullable=False, server_default=text("1"))

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")


# Subscription Model
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_subscription_id = Column(String, unique=True, nullable=False)
    plan = Column(Enum(PlanEnum), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="subscriptions")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    template = Column(String)
    payload = Column(JSON)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")

from pydantic import BaseModel
from typing import List



class EducationItem(BaseModel):
    school: str
    degree: str
    years: str

class ExperienceItem(BaseModel):
    company: str
    role: str
    years: str
    descriptions: List[str]

class SkillsItem(BaseModel):
    programmingLanguages: List[str] = []
    frameworks: List[str] = []
    developerTools: List[str] = []

class HarvardResumeInput(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    education: List[EducationItem]
    experience: List[ExperienceItem]
    skills: SkillsItem
############################################
class Experience(BaseModel):
    company: Optional[str] = ""
    role: Optional[str] = ""
    year: Optional[str] = ""
    description: Optional[str] = ""

class Leadership(BaseModel):
    leadership: Optional[str] = ""
    role: Optional[str] = ""
    year: Optional[str] = ""
    description: Optional[str] = ""

class Award(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""


class MITResumeInput(BaseModel):
    name: str
    school: str
    topheader: str
    degree: str
    graduationYear: str
    courses: List[str]
    experiences: List[Experience]
    leadership: List[Leadership]
    skills: List[str]
    awards: List[Award]
############################################
class ExperienceYale(BaseModel):
    company: str
    role: Optional[str] = None
    location: Optional[str] = None
    dates: Optional[str] = None
    bullets: List[str] = []

class Education(BaseModel):
    university: Optional[str] = None
    university_location: Optional[str] = None
    degree: Optional[str] = None
    graduation_month_year: Optional[str] = None
    university_courses: List[str] = []
    university_awards: List[str] = []

    highschool: Optional[str] = None
    highschool_location: Optional[str] = None
    highschool_graduation: Optional[str] = None
    highschool_awards: List[str] = []

class YaleResumeInput(BaseModel):
    full_name: str                   # required
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None

    education: Education             # required nested object

    public_section_description: Optional[str] = None
    experiences: List[ExperienceYale] = []
    additional_section_description: Optional[str] = None
    additional_experiences: List[ExperienceYale] = []

    computer_skills: List[str] = []
    language_skills: List[str] = []
############################################
class StanfordExperience(BaseModel):
    company: str
    location: str
    role: str
    years: str
    bullets: List[str]

class StanfordEducation(BaseModel):
    school: str
    location: str
    degree: str
    highlights: List[str]

class StanfordResumeInput(BaseModel):
    name: str  # maps to full_name in frontend
    address: str
    city_state_zip: str
    phone: str
    email: str
    experiences: List[StanfordExperience]
    education: StanfordEducation
    additional: List[str]
############################################
class CelestialAddress(BaseModel):
    street: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    country: str = ""

class CelestialEducation(BaseModel):
    school: str
    location: str
    dates: str
    degree: str

class CelestialExperience(BaseModel):
    role: str
    company: str
    location: str
    dates: str
    bullets: List[str] = []

class CelestialResumeInput(BaseModel):
    # Header / top info
    name: str
    title: str
    header_summary: str
    email: str
    phone: str
    location: str  # You can keep this for fallback

    # Address object for LaTeX template
    address: CelestialAddress = CelestialAddress()

    # Sections
    education: List[CelestialEducation] = []
    skills: List[str] = []
    experience: List[CelestialExperience] = []

############################################
class MonochromeEducation(BaseModel):
    degree: str
    school: str
    location: str
    dates: str

class MonochromeExperience(BaseModel):
    role: str
    company: str
    location: str
    dates: str
    bullets: List[str] = []

class MonochromeResumeInput(BaseModel):
    # Header / top info
    name: str
    title: str
    email: str
    phone: str
    address: dict  # e.g., {"street": "...", "city": "...", "state": "...", "zip": "...", "country": "..."}

    # Sections
    summary: str
    education: List[MonochromeEducation] = []
    skills: List[str] = []
    experience: List[MonochromeExperience] = []
############################################
class NebulaEducation(BaseModel):
    school: str
    location: str
    dates: str
    degree: str

class NebulaExperience(BaseModel):
    role: str
    company: str
    location: str
    dates: str
    bullets: List[str] = []

class NebulaResumeInput(BaseModel):
    # Header / top info
    name: str
    title: str
    header_summary: str
    email: str
    phone: str
    location: str  # Could be "City, State" or full string

    # Sections
    education: List[NebulaEducation] = []
    skills: List[str] = []
    experience: List[NebulaExperience] = []
############################################
class CosmosAddress(BaseModel):
    street: str
    city: str
    state: str
    zip: str
    country: str

class CosmosEducation(BaseModel):
    degree: str
    school: str
    location: str
    dates: str

class CosmosExperience(BaseModel):
    role: str
    company: str
    location: str
    dates: str
    bullets: List[str] = []

class CosmosResumeInput(BaseModel):
    # Header / top info
    name: str
    title: str
    email: str
    phone: str
    address: CosmosAddress

    # Sections
    summary: str
    experience: List[CosmosExperience] = []
    education: List[CosmosEducation] = []
    skills: List[str] = []

##########################################
class GenerateRequest(BaseModel):
    resume: str
    job_description: str
