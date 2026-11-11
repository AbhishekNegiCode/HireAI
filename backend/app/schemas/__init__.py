from datetime import date
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator


class Register(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    confirm_password: str
    role: Literal["candidate", "recruiter"]

    @model_validator(mode="after")
    def passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords must match")
        return self


class Login(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class EducationInput(BaseModel):
    institution: str = Field(min_length=1, max_length=200)
    degree: str = Field(min_length=1, max_length=200)
    start_year: int = Field(ge=1900, le=2200)
    end_year: int | None = Field(default=None, ge=1900, le=2200)

    @model_validator(mode="after")
    def dates(self):
        if self.end_year is not None and self.end_year < self.start_year:
            raise ValueError("End year must follow start year")
        return self


class ExperienceInput(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date must follow start date")
        return self


class ProfileInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(default="", max_length=40)
    location: str = Field(default="", max_length=160)
    headline: str = Field(default="", max_length=200)
    professional_summary: str = Field(default="", max_length=10000)
    total_experience: float = Field(default=0, ge=0, le=80)
    portfolio_url: str = Field(default="", max_length=500)
    linkedin_url: str = Field(default="", max_length=500)
    github_url: str = Field(default="", max_length=500)
    education: list[EducationInput] = Field(default_factory=list, max_length=30)
    experience: list[ExperienceInput] = Field(default_factory=list, max_length=50)

    @field_validator("portfolio_url", "linkedin_url", "github_url")
    @classmethod
    def urls(cls, v):
        if v and not v.startswith(("https://", "http://")):
            raise ValueError("Use a complete http(s) URL")
        return v


class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    proficiency_level: Literal["Beginner", "Intermediate", "Advanced", "Expert"] = (
        "Intermediate"
    )
    years_of_experience: float = Field(default=0, ge=0, le=80)


class JobSkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    importance: int = Field(default=3, ge=1, le=5)
    is_required: bool = True


class JobInput(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=30, max_length=30000)
    responsibilities: str = Field(default="", max_length=20000)
    employment_type: Literal["Full-time", "Part-time", "Contract", "Internship"] = (
        "Full-time"
    )
    experience_min: float = Field(default=0, ge=0, le=80)
    experience_max: float = Field(default=10, ge=0, le=80)
    salary_min: int = Field(default=0, ge=0)
    salary_max: int = Field(default=0, ge=0)
    location: str = Field(min_length=1, max_length=160)
    work_mode: Literal["Remote", "Hybrid", "On-site"] = "Remote"
    status: Literal["active", "closed", "draft"] = "active"
    application_deadline: date | None = None
    skills: list[JobSkillInput] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def ranges(self):
        if (
            self.experience_max < self.experience_min
            or self.salary_max < self.salary_min
        ):
            raise ValueError("Maximum must be at least the minimum")
        return self


class CompanyInput(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=10000)
    website: str = Field(default="", max_length=500)
    industry: str = Field(default="", max_length=100)
    company_size: str = Field(default="", max_length=50)
    location: str = Field(default="", max_length=160)
    logo_url: str = Field(default="", max_length=500)

    @field_validator("website", "logo_url")
    @classmethod
    def urls(cls, v):
        if v and not v.startswith(("https://", "http://")):
            raise ValueError("Use a complete http(s) URL")
        return v


class ApplicationInput(BaseModel):
    job_id: int
    cover_letter: str = Field(default="", max_length=10000)


class StatusInput(BaseModel):
    status: Literal[
        "Under Review", "Shortlisted", "Interview Scheduled", "Selected", "Rejected"
    ]


class ActiveInput(BaseModel):
    is_active: bool


class ReportInput(BaseModel):
    reason: str = Field(min_length=10, max_length=5000)


class ReportStatus(BaseModel):
    status: Literal["resolved", "dismissed"]


class ResumeOutput(BaseModel):
    candidate_name: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=254)
    education: list[EducationInput] = Field(default_factory=list, max_length=30)
    technical_skills: list[str] = Field(default_factory=list, max_length=100)
    soft_skills: list[str] = Field(default_factory=list, max_length=50)
    projects: list[str] = Field(default_factory=list, max_length=50)
    work_experience: list[ExperienceInput] = Field(default_factory=list, max_length=50)
    total_experience: float = Field(default=0, ge=0, le=80)
    certifications: list[str] = Field(default_factory=list, max_length=50)
    suggested_roles: list[str] = Field(default_factory=list, max_length=15)
    professional_summary: str = Field(default="", max_length=5000)

    @field_validator(
        "technical_skills",
        "soft_skills",
        "certifications",
        "suggested_roles",
        "projects",
    )
    @classmethod
    def clean(cls, values):
        unique = {}
        for value in values:
            value = " ".join(value.split())[:500]
            if value:
                unique.setdefault(value.casefold(), value)
        return list(unique.values())
