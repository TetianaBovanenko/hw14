from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from passlib.hash import bcrypt  # For password hashing (optional, you can adjust)

Base = declarative_base()


class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    second_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    birthdate = Column(Date, nullable=False)
    additional_data = Column(String(255), nullable=True)
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    # Establishing the relationship with the User table
    user = relationship('User', back_populates='contacts')

    # Additional constraints (optional): Ensure unique contact information
    __table_args__ = (UniqueConstraint('email', 'phone', name='_contact_email_phone_uc'),)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Storing hashed password
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String, nullable=True)
    confirmed = Column(Boolean, default=False)

    # Establishing the relationship with the Contact table
    contacts = relationship('Contact', back_populates='user', cascade='all, delete-orphan')

    def hash_password(self, password):
        """Hash the user's password for secure storage."""
        self.password = bcrypt.hash(password)

    def verify_password(self, password):
        """Verify the provided password against the stored hash."""
        return bcrypt.verify(password, self.password)
