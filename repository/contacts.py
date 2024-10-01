from typing import Optional, List
from sqlalchemy import extract, cast, Date, and_
from sqlalchemy.orm import Session
from db.models import Contact, User
from schemas import ContactCreate
from datetime import date, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_contacts(db: Session, user: User, skip: int = 0, limit: int = 100) -> List[Contact]:
    """
    Retrieves a list of contacts for a specific user with pagination options.
    """
    return db.query(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit).all()


def get_contact(db: Session, contact_id: int, user: User) -> Optional[Contact]:
    """
    Retrieves a specific contact by ID for a user.
    """
    return db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()


def create_contact(db: Session, contact: ContactCreate, user: User) -> Contact:
    """
    Creates a new contact for a user.
    """
    db_contact = Contact(**contact.dict(), user_id=user.id)
    db.add(db_contact)
    try:
        db.commit()
        db.refresh(db_contact)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating contact for user {user.id}: {e}")
        raise
    return db_contact


def upgrade_contact(db: Session, user: User, contact_id: int, contact: ContactCreate) -> Optional[Contact]:
    """
    Updates an existing contact for a user.
    """
    db_contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if db_contact:
        try:
            for key, value in contact.dict().items():
                setattr(db_contact, key, value)
            db.commit()
            db.refresh(db_contact)
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating contact {contact_id} for user {user.id}: {e}")
            raise
    return db_contact


def delete_contact(db: Session, user: User, contact_id: int) -> Optional[Contact]:
    """
    Deletes a contact for a specific user.
    """
    db_contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if db_contact:
        try:
            db.delete(db_contact)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting contact {contact_id} for user {user.id}: {e}")
            raise
        return db_contact
    return None


def search_contacts(db: Session, user: User, first_name: Optional[str] = None,
                    second_name: Optional[str] = None, email: Optional[str] = None) -> List[Contact]:
    """
    Searches for contacts based on first name, last name, or email.
    """
    query = db.query(Contact).filter(Contact.user_id == user.id)
    if first_name:
        query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if second_name:
        query = query.filter(Contact.second_name.ilike(f"%{second_name}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    return query.all()


def get_upcoming_birthdays(db: Session, user: User) -> List[Contact]:
    """
    Retrieves contacts with upcoming birthdays within the next 7 days.
    """
    today = date.today()
    seven_days_later = today + timedelta(days=7)

    # Contacts with upcoming birthdays in the current month
    contacts_with_upcoming_birthdays = db.query(Contact).filter(
        Contact.user_id == user.id,
        extract('month', cast(Contact.birthdate, Date)) == today.month,
        extract('day', cast(Contact.birthdate, Date)) >= today.day,
        extract('day', cast(Contact.birthdate, Date)) <= seven_days_later.day
    ).all()

    # Handle birthdays crossing into the next month
    if today.month != seven_days_later.month:
        contacts_with_upcoming_birthdays += db.query(Contact).filter(
            Contact.user_id == user.id,
            extract('month', cast(Contact.birthdate, Date)) == seven_days_later.month,
            extract('day', cast(Contact.birthdate, Date)) <= seven_days_later.day
        ).all()

    return contacts_with_upcoming_birthdays
