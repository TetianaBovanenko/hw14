from fastapi import APIRouter, HTTPException, status, Depends, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from schemas import UserCreate, UserResponse, TokenModel, RequestEmail
from db.connect_db import get_db
from services.auth import auth_services
from services.email import send_email
import repository
import logging

# Initialize router and security
router = APIRouter()
security = HTTPBearer()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Registers a new user.

    :raises HTTPException: If email is already registered.
    """
    exist_user = repository.users.get_user_by_email(user.email, db)
    if exist_user:
        logger.warning(f"Registration attempt with already registered email: {user.email}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Hash the password before storing it
    user.password = auth_services.hash_password(user.password)
    new_user = repository.users.create_user(db, user)

    # Queue the confirmation email
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    logger.info(f"User registered successfully: {new_user.email}")

    return new_user


@router.post('/login', response_model=TokenModel, status_code=status.HTTP_201_CREATED)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Logs a user in and returns access and refresh tokens.

    :raises HTTPException: If credentials are invalid or email is not confirmed.
    """
    user = repository.users.get_user_by_email(form_data.username, db)

    if user is None:
        logger.warning(f"Login attempt with invalid email: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")

    if not user.confirmed:
        logger.warning(f"Login attempt for unconfirmed email: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")

    if not auth_services.verify_password(form_data.password, user.password):
        logger.warning(f"Login attempt with invalid password for email: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    access_token = auth_services.create_access_token(data={'sub': user.email})
    refresh_token = auth_services.create_refresh_token(data={'sub': user.email})
    repository.users.update_token(user, refresh_token, db)

    logger.info(f"User logged in successfully: {user.email}")

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post('/request_email')
def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                  db: Session = Depends(get_db)):
    """
    Sends a confirmation email to the user.

    :raises HTTPException: If email is already confirmed.
    """
    user = repository.users.get_user_by_email(body.email, db)

    if not user:
        logger.warning(f"Email confirmation request for non-existent user: {body.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.confirmed:
        logger.info(f"Email already confirmed for user: {user.email}")
        return {"message": "Your email is already confirmed"}

    # Queue the confirmation email
    background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    logger.info(f"Confirmation email sent to: {user.email}")

    return {"message": "Check your email for confirmation."}


@router.get('/refresh_token', response_model=TokenModel, status_code=status.HTTP_201_CREATED)
def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    Refreshes access token using the refresh token.

    :raises HTTPException: If refresh token is invalid.
    """
    token = credentials.credentials
    try:
        email = auth_services.decode_refresh_token(token)
    except Exception as e:
        logger.warning(f"Invalid refresh token: {token}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = repository.users.get_user_by_email(email, db)

    if user is None or user.refresh_token != token:
        logger.warning(f"Refresh token mismatch for user: {email}")
        repository.users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = auth_services.create_access_token(data={"sub": email})
    refresh_token = auth_services.create_refresh_token(data={"sub": email})

    repository.users.update_token(user, refresh_token, db)
    logger.info(f"Refresh token used successfully for user: {user.email}")

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirms the user's email using a confirmation token.

    :raises HTTPException: If the token is invalid or the user does not exist.
    """
    try:
        email = auth_services.get_email_from_token(token)
    except Exception as e:
        logger.error(f"Invalid confirmation token: {token}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")

    user = repository.users.get_user_by_email(email, db)

    if user is None:
        logger.warning(f"Email confirmation attempt for non-existent user: {email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")

    if user.confirmed:
        logger.info(f"Email already confirmed for user: {user.email}")
        return {"message": "Your email is already confirmed"}

    repository.users.confirmed_email(email, db)
    logger.info(f"Email confirmed successfully for user: {user.email}")

    return {"message": "Email confirmed"}
