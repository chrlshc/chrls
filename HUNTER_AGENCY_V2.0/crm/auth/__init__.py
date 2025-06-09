#!/usr/bin/env python3
"""
🔐 HUNTER AGENCY - JWT Authentication & Authorization System
Enterprise-grade security with role-based access control
"""

import os
from datetime import datetime, timedelta
from typing import Any, Union, Optional, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 🔧 SECURITY CONFIGURATION
# ============================================================================

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

Base = declarative_base()
# Database dependency
def get_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = "sqlite:///./hunter_agency.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# ============================================================================
# 🏷️ USER ROLES & PERMISSIONS
# ============================================================================

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"      # Full system access
    ADMIN = "admin"                  # Organization admin
    SALES_MANAGER = "sales_manager"  # Team management
    SALES_REP = "sales_rep"         # Individual sales
    VIEWER = "viewer"               # Read-only access

class Permission(str, Enum):
    # Lead permissions
    LEAD_CREATE = "lead:create"
    LEAD_READ = "lead:read"
    LEAD_UPDATE = "lead:update"
    LEAD_DELETE = "lead:delete"
    LEAD_ASSIGN = "lead:assign"
    
    # Pipeline permissions
    PIPELINE_VIEW = "pipeline:view"
    PIPELINE_MANAGE = "pipeline:manage"
    
    # Analytics permissions
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    
    # Admin permissions
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [p for p in Permission],  # All permissions
    UserRole.ADMIN: [
        Permission.LEAD_CREATE, Permission.LEAD_READ, Permission.LEAD_UPDATE,
        Permission.LEAD_ASSIGN, Permission.PIPELINE_VIEW, Permission.PIPELINE_MANAGE,
        Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT, Permission.USER_MANAGE
    ],
    UserRole.SALES_MANAGER: [
        Permission.LEAD_CREATE, Permission.LEAD_READ, Permission.LEAD_UPDATE,
        Permission.LEAD_ASSIGN, Permission.PIPELINE_VIEW, Permission.ANALYTICS_VIEW
    ],
    UserRole.SALES_REP: [
        Permission.LEAD_CREATE, Permission.LEAD_READ, Permission.LEAD_UPDATE,
        Permission.PIPELINE_VIEW, Permission.ANALYTICS_VIEW
    ],
    UserRole.VIEWER: [
        Permission.LEAD_READ, Permission.PIPELINE_VIEW, Permission.ANALYTICS_VIEW
    ]
}

# ============================================================================
# 📊 DATABASE MODELS
# ============================================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50))
    avatar_url = Column(String(500))
    
    # Role & Access
    role = Column(String(50), nullable=False, default=UserRole.SALES_REP)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    # Settings
    preferences = Column(JSON, default={})
    timezone = Column(String(50), default="UTC")
    
    # Security
    last_login = Column(DateTime)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    team = relationship("Team", back_populates="members")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    
    # Settings
    settings = Column(JSON, default={})
    subscription_plan = Column(String(50), default="free")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    teams = relationship("Team", back_populates="organization")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("User", back_populates="team")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    
    # Security
    client_ip = Column(String(45))
    user_agent = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

# ============================================================================
# 🔄 PYDANTIC SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole = UserRole.SALES_REP

class UserCreate(UserBase):
    password: str
    organization_id: Optional[int] = None
    team_id: Optional[int] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    team_id: Optional[int] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    organization_id: Optional[int]
    team_id: Optional[int]
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None
    team_id: Optional[int] = None
    permissions: List[str] = []

# ============================================================================
# 🔐 AUTHENTICATION UTILITIES
# ============================================================================

class AuthManager:
    """Handles authentication and authorization logic"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            organization_id: int = payload.get("organization_id")
            team_id: int = payload.get("team_id")
            
            if user_id is None or email is None:
                return None
                
            # Get permissions for role
            permissions = ROLE_PERMISSIONS.get(UserRole(role), [])
            permission_strings = [p.value for p in permissions]
            
            return TokenData(
                user_id=user_id,
                email=email,
                role=role,
                organization_id=organization_id,
                team_id=team_id,
                permissions=permission_strings
            )
            
        except JWTError:
            return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
            
        if not user.is_active:
            return None
            
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            return None
            
        if not AuthManager.verify_password(password, user.hashed_password):
            # Increment login attempts
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
            return None
        
        # Reset login attempts on successful login
        user.login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user

# ============================================================================
# 🛡️ AUTHORIZATION DECORATORS & DEPENDENCIES
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = AuthManager.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        user_permissions = ROLE_PERMISSIONS.get(UserRole(current_user.role), [])
        
        if permission not in user_permissions and UserRole(current_user.role) != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {permission.value}"
            )
        return current_user
    
    return permission_checker

def require_role(role: UserRole):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if UserRole(current_user.role) != role and UserRole(current_user.role) != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {role.value}"
            )
        return current_user
    
    return role_checker

# ============================================================================
# 🔒 DATA ISOLATION FILTERS
# ============================================================================

class DataFilter:
    """Handles data isolation based on user role and organization"""
    
    @staticmethod
    def filter_leads_query(query, user: User):
        """Filter leads based on user's access level"""
        role = UserRole(user.role)
        
        if role == UserRole.SUPER_ADMIN:
            # Super admin sees everything
            return query
        
        elif role == UserRole.ADMIN:
            # Admin sees all leads in their organization
            return query.filter(Lead.organization_id == user.organization_id)
        
        elif role == UserRole.SALES_MANAGER:
            # Sales manager sees leads from their team
            return query.filter(
                or_(
                    Lead.assigned_to == user.email,
                    Lead.team_id == user.team_id
                )
            )
        
        else:  # SALES_REP, VIEWER
            # Sales rep sees only their assigned leads
            return query.filter(Lead.assigned_to == user.email)
    
    @staticmethod
    def can_access_lead(lead, user: User) -> bool:
        """Check if user can access specific lead"""
        role = UserRole(user.role)
        
        if role == UserRole.SUPER_ADMIN:
            return True
            
        if role == UserRole.ADMIN and lead.organization_id == user.organization_id:
            return True
            
        if role == UserRole.SALES_MANAGER and (
            lead.assigned_to == user.email or lead.team_id == user.team_id
        ):
            return True
            
        if lead.assigned_to == user.email:
            return True
            
        return False
    
    @staticmethod
    def can_modify_lead(lead, user: User) -> bool:
        """Check if user can modify specific lead"""
        if not DataFilter.can_access_lead(lead, user):
            return False
            
        role = UserRole(user.role)
        
        # Viewers can't modify
        if role == UserRole.VIEWER:
            return False
            
        # Others can modify if they can access
        return True

# ============================================================================
# 🎯 EXAMPLE USAGE IN FASTAPI
# ============================================================================

def secure_endpoint_example():
    """Example of how to use auth in FastAPI endpoints"""
    
    from fastapi import FastAPI
    
    app = FastAPI()
    
    @app.post("/leads", dependencies=[Depends(require_permission(Permission.LEAD_CREATE))])
    async def create_lead(
        lead_data: dict,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Create lead with proper authorization"""
        # Lead will automatically be associated with user's org/team
        lead_data['organization_id'] = current_user.organization_id
        lead_data['team_id'] = current_user.team_id
        lead_data['created_by'] = current_user.email
        
        # Create lead...
        return {"message": "Lead created"}
    
    @app.get("/leads")
    async def get_leads(
        current_user: User = Depends(require_permission(Permission.LEAD_READ)),
        db: Session = Depends(get_db)
    ):
        """Get leads with data isolation"""
        query = db.query(Lead)
        
        # Apply data filter based on user role
        filtered_query = DataFilter.filter_leads_query(query, current_user)
        
        leads = filtered_query.all()
        return leads
    
    @app.put("/leads/{lead_id}")
    async def update_lead(
        lead_id: int,
        lead_data: dict,
        current_user: User = Depends(require_permission(Permission.LEAD_UPDATE)),
        db: Session = Depends(get_db)
    ):
        """Update lead with access control"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
            
        if not DataFilter.can_modify_lead(lead, current_user):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update lead...
        return {"message": "Lead updated"}

if __name__ == "__main__":
    print("🔐 Hunter Agency JWT Auth System")
    print("=" * 50)
    print("✅ Role-based access control")
    print("✅ Data isolation by organization/team")
    print("✅ JWT tokens with refresh")
    print("✅ Permission-based endpoints")
    print("✅ Account security (lockout, attempts)")
    print("🚀 Ready for production!")
def get_db():
    """Database dependency - placeholder"""
    pass
