"""
SQLAlchemy ORM models for ChamaYetu application.

Models:
- User: Application users (members and admins)
- Group: Chama groups with contribution settings
- GroupMember: Junction table tracking member queue positions
- Cycle: Contribution cycles (one round of merry-go-round)
- Contribution: Individual member payments per cycle
- Payout: B2C disbursements to beneficiaries
- Notification: User notifications
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Enum as SQLEnum, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# Enums for status fields
class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class GroupStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    completed = "completed"


class GroupFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class CycleStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    disbursed = "disbursed"


class ContributionStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"


class PayoutStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class User(Base):
    """
    User model - represents application users.
    
    Users can be regular members or admins. Admin role is stored in the database
    but authentication determines actual admin privileges.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)  # Format: 2547XXXXXXXX
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.member, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    groups_created = relationship("Group", back_populates="creator", foreign_keys="Group.created_by")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
    contributions = relationship("Contribution", back_populates="user", cascade="all, delete-orphan")
    payouts_received = relationship("Payout", back_populates="recipient", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Group(Base):
    """
    Group model - represents a Chama (savings group).
    
    Groups have contribution amounts, frequencies, and member limits.
    The invite_code is an 8-character code used for members to join.
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    contribution_amount = Column(Float, nullable=False)  # Amount in KES
    frequency = Column(SQLEnum(GroupFrequency), nullable=False)
    max_members = Column(Integer, nullable=False, default=10)
    invite_code = Column(String(8), unique=True, index=True, nullable=False)
    status = Column(SQLEnum(GroupStatus), default=GroupStatus.active, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="groups_created", foreign_keys=[created_by])
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    cycles = relationship("Cycle", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """
    GroupMember junction table - tracks which users belong to which groups.
    
    Also stores the queue position (turn order) for the merry-go-round rotation
    and whether the member has already received their payout.
    """
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    queue_position = Column(Integer, nullable=False)  # 1-based turn order
    has_received = Column(Boolean, default=False, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    # Constraints
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member"),
        UniqueConstraint("group_id", "queue_position", name="uq_group_queue"),
    )


class Cycle(Base):
    """
    Cycle model - represents one complete round of contributions.
    
    Each cycle has a beneficiary who receives the total collected amount.
    Cycles go through statuses: pending → active → completed → disbursed
    """
    __tablename__ = "cycles"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    cycle_number = Column(Integer, nullable=False)  # 1, 2, 3...
    beneficiary_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(CycleStatus), default=CycleStatus.pending, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    total_collected = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("Group", back_populates="cycles")
    beneficiary = relationship("User")
    contributions = relationship("Contribution", back_populates="cycle", cascade="all, delete-orphan")
    payout = relationship("Payout", back_populates="cycle", uselist=False, cascade="all, delete-orphan")


class Contribution(Base):
    """
    Contribution model - represents one member's payment in a cycle.
    
    Tracks STK Push requests and M-Pesa receipt numbers.
    Status flows: pending → confirmed | failed
    """
    __tablename__ = "contributions"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(ContributionStatus), default=ContributionStatus.pending, nullable=False)
    mpesa_checkout_id = Column(String(100), nullable=True)  # STK Push CheckoutRequestID
    mpesa_receipt_number = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=False)
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)

    # Relationships
    cycle = relationship("Cycle", back_populates="contributions")
    user = relationship("User", back_populates="contributions")


class Payout(Base):
    """
    Payout model - represents B2C disbursement to the cycle beneficiary.
    
    Tracks B2C payment requests and transaction IDs from M-Pesa.
    Status flows: pending → processing → completed | failed
    """
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), unique=True, nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(PayoutStatus), default=PayoutStatus.pending, nullable=False)
    mpesa_conversation_id = Column(String(100), nullable=True)
    mpesa_transaction_id = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=False)
    initiated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    failure_reason = Column(String(255), nullable=True)

    # Relationships
    cycle = relationship("Cycle", back_populates="payout")
    recipient = relationship("User", back_populates="payouts_received")


class Notification(Base):
    """
    Notification model - stores user notifications.
    
    Notifications are created for events like:
    - New cycle started
    - Contribution reminder
    - Payout received
    - Group invitation
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
