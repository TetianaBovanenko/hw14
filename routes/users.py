import os
import cloudinary
import cloudinary.uploader
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from db.connect_db import get_db
from db.models import User
from repository import users as repository_users
from services.auth import auth_services
from schemas import UserResponse
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(auth_services.get_current_user)):
    """
    Returns the current authenticated user's data.
    """
    return current_user


@router.patch('/avatar', response_model=UserResponse)
async def update_avatar_user(file: UploadFile = File(...), current_user: User = Depends(auth_services.get_current_user),
                             db: Session = Depends(get_db)):
    """
    Updates the avatar of the current user by uploading the image to Cloudinary.

    :param file: The uploaded image file for the new avatar.
    :param current_user: The currently authenticated user.
    :param db: Database session.
    :return: The updated user data with the new avatar URL.
    """
    # Check the file type (optional but recommended)
    ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/jpg"}
    if file.content_type not in ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported file type: {file.content_type}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type.")

    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )

    try:
        # Upload the file to Cloudinary
        logger.info(f"Uploading avatar for user {current_user.username} to Cloudinary.")
        upload_result = cloudinary.uploader.upload(
            file.file,
            public_id=f'NotesApp/{current_user.username}',
            overwrite=True
        )
    except Exception as e:
        logger.error(f"Error uploading avatar to Cloudinary: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload avatar.")

    # Generate the URL for the uploaded avatar
    try:
        src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.username}')\
            .build_url(width=250, height=250, crop='fill', version=upload_result.get('version'))
        logger.info(f"Avatar URL generated: {src_url}")
    except Exception as e:
        logger.error(f"Error generating Cloudinary image URL: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate avatar URL.")

    # Update the avatar URL in the database
    try:
        user = repository_users.update_avatar(current_user.email, src_url, db)
        logger.info(f"Avatar updated for user {current_user.email}")
        return user
    except Exception as e:
        logger.error(f"Error updating avatar in the database: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update avatar.")
