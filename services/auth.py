import os
from datetime import timedelta, datetime
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db.connect_db import get_db
from repository import users

load_dotenv()


class Auth:
    """
    A class to handle authentication, including password hashing, token creation, and verification.

    Attributes:
        pwd_context (CryptContext): Context for hashing passwords using bcrypt.
        SECRET_KEY (str): Secret key for encoding and decoding JWT tokens.
        ALGORITHM (str): Algorithm used for encoding and decoding JWT tokens.
        oauth2_scheme (OAuth2PasswordBearer): Dependency for OAuth2 password flow.
    """

    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

    if not SECRET_KEY or not ALGORITHM:
        raise ValueError("SECRET_KEY or ALGORITHM environment variables not set")

    def hash_password(self, password: str) -> str:
        """
        Hashes a plain password using bcrypt.

        :param password: Plain password to hash.
        :return: Hashed password.
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain password against a hashed password.

        :param plain_password: Plain password for verification.
        :param hashed_password: Hashed password for comparison.
        :return: True if passwords match, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """
        Creates an access JWT token.

        :param data: Data to encode in the token.
        :param expires_delta: Expiration time for the token. Defaults to 30 minutes.
        :return: Encoded access token.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
        to_encode.update({'exp': expire, 'scope': 'access_token'})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_refresh_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """
        Creates a refresh JWT token.

        :param data: Data to encode in the token.
        :param expires_delta: Expiration time for the token. Defaults to 7 days.
        :return: Encoded refresh token.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
        to_encode.update({'exp': expire, 'scope': 'refresh_token'})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_refresh_token(self, refresh_token: str) -> str:
        """
        Decodes and validates a refresh token.

        :param refresh_token: Refresh token to decode.
        :return: Email encoded in the token if valid.
        :raises HTTPException: If the token is invalid or the scope is incorrect.
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get('scope') != 'refresh_token':
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token scope')
            return payload['sub']
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')

    def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        """
        Retrieves the current user based on the provided access token.

        :param token: Access token for decoding.
        :param db: Database session dependency.
        :return: User associated with the token.
        :raises HTTPException: If the token is invalid or the user does not exist.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get('scope') != 'access_token':
                raise credentials_exception
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")
        except JWTError:
            raise credentials_exception

        user = users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user

    def create_email_token(self, data: dict) -> str:
        """
        Creates a JWT token for email verification.

        :param data: Data to encode in the token.
        :return: Encoded email verification token.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def get_email_from_token(self, token: str) -> str:
        """
        Retrieves the email from a verification token.

        :param token: Token to decode.
        :return: Email encoded in the token.
        :raises HTTPException: If the token is invalid or expired.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload.get("sub")
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email token expired")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid email token")


auth_services = Auth()
