from libgravatar import Gravatar
from sqlalchemy.orm import Session
from db.models import User
from schemas import UserCreate
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_by_email(email: str, db: Session) -> Optional[User]:
    """
    Retrieves a user from the database by their email address.

    :param email: The email address of the user to retrieve.
    :param db: The database session used for querying the user.
    :return: The user object if found, or None if no user is associated with the provided email.
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        logger.info(f"User found: {email}")
    else:
        logger.warning(f"User not found: {email}")
    return user


def create_user(db: Session, user: UserCreate) -> User:
    """
    Creates a new user with the provided details, including an optional Gravatar image.

    :param db: The database session used for adding the new user.
    :param user: The user creation schema with details like email, password, etc.
    :return: The created user object.
    """
    avatar = None
    try:
        g = Gravatar(user.email)
        avatar = g.get_image()
        logger.info(f"Gravatar image retrieved for user: {user.email}")
    except Exception as e:
        logger.error(f"Error retrieving Gravatar for {user.email}: {e}")
        avatar = None  # Fallback to None if Gravatar fetch fails

    new_user = User(**user.dict(), avatar=avatar)
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
        logger.info(f"User created: {new_user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user {user.email}: {e}")
        raise
    return new_user


def update_token(user: User, token: Optional[str], db: Session) -> None:
    """
    Updates the refresh token for a specific user.

    :param user: The user whose token needs to be updated.
    :param token: The new refresh token or None to clear it.
    :param db: The database session used for committing changes.
    """
    user.refresh_token = token
    try:
        db.commit()
        logger.info(f"Refresh token updated for user: {user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating token for user {user.email}: {e}")
        raise


def confirmed_email(email: str, db: Session) -> None:
    """
    Marks a user's email as confirmed.

    :param email: The email address of the user to confirm.
    :param db: The database session used for committing changes.
    """
    user = get_user_by_email(email, db)
    if user:
        user.confirmed = True
        try:
            db.commit()
            logger.info(f"User email confirmed: {email}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error confirming email for {email}: {e}")
            raise
    else:
        logger.warning(f"Attempt to confirm email for non-existing user: {email}")


def update_avatar(email: str, url: str, db: Session) -> Optional[User]:
    """
    Updates the avatar of a user using a provided URL.

    :param email: The email address of the user whose avatar needs to be updated.
    :param url: The URL of the new avatar image.
    :param db: The database session used for committing changes.
    :return: The updated user object, or None if the user is not found.
    """
    user = get_user_by_email(email, db)
    if user:
        user.avatar = url
        try:
            db.commit()
            logger.info(f"Avatar updated for user: {email}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating avatar for user {email}: {e}")
            raise
        return user
    else:
        logger.warning(f"Attempt to update avatar for non-existing user: {email}")
        return None
