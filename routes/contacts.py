from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from db.connect_db import get_db
from db.models import User
from repository import contacts
from schemas import Contact, ContactCreate
from services.auth import auth_services
from services.rate_limits import limit_rate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/contacts')


@router.post('/', response_model=Contact, status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(auth_services.get_current_user)):
    """
    Creates a new contact for the current user.
    """
    limit_rate(current_user.id)
    db_contact = contacts.create_contact(db=db, contact=contact, user=current_user)
    logger.info(f"Contact created for user {current_user.id}: {db_contact.id}")
    return db_contact


@router.get("/birthday_next_7_days", response_model=list[Contact])
def get_contacts_birthday_next_7_days(db: Session = Depends(get_db),
                                      current_user: User = Depends(auth_services.get_current_user)):
    """
    Retrieves the current user's contacts with upcoming birthdays within the next 7 days.
    """
    contacts_list = contacts.get_upcoming_birthdays(db, current_user)
    logger.info(f"Found {len(contacts_list)} upcoming birthdays for user {current_user.id}")
    return contacts_list


@router.get("/search", response_model=list[Contact])
def search_contacts(first_name: str = None, second_name: str = None, email: str = None,
                    db: Session = Depends(get_db), current_user: User = Depends(auth_services.get_current_user)):
    """
    Searches the current user's contacts by first name, last name, or email.
    """
    results = contacts.search_contacts(db, current_user, first_name=first_name, second_name=second_name, email=email)
    logger.info(f"Search results for user {current_user.id}: {len(results)} contacts found")
    return results


@router.get('/{contact_id}', response_model=Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(auth_services.get_current_user)):
    """
    Retrieves the contact details by its ID.
    """
    db_contact = contacts.get_contact(db, contact_id, current_user)
    if db_contact is None:
        logger.warning(f"Contact {contact_id} not found for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    logger.info(f"Contact {contact_id} retrieved for user {current_user.id}")
    return db_contact


@router.get('/', response_model=list[Contact])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                  current_user: User = Depends(auth_services.get_current_user)):
    """
    Retrieves the current user's contacts with pagination options.
    """
    db_contacts = contacts.get_contacts(db, current_user, skip=skip, limit=limit)
    if not db_contacts:
        logger.warning(f"No contacts found for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No contacts found')
    logger.info(f"Found {len(db_contacts)} contacts for user {current_user.id}")
    return db_contacts


@router.put('/{contact_id}', response_model=Contact)
def update_contact(contact_id: int, contact_update: ContactCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(auth_services.get_current_user)):
    """
    Updates a contact by its ID.
    """
    db_contact = contacts.upgrade_contact(db, current_user, contact_id, contact_update)
    if db_contact is None:
        logger.warning(f"Failed to update: Contact {contact_id} not found for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    logger.info(f"Contact {contact_id} updated for user {current_user.id}")
    return db_contact


@router.delete('/{contact_id}', response_model=Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(auth_services.get_current_user)):
    """
    Deletes a contact by its ID.
    """
    db_contact = contacts.delete_contact(db, current_user, contact_id)
    if db_contact is None:
        logger.warning(f"Failed to delete: Contact {contact_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Contact not found")
    logger.info(f"Contact {contact_id} deleted for user {current_user.id}")
    return db_contact
