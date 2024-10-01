import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from services.auth import auth_services
import logging

# Load environment variables from the .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure all necessary environment variables are set
required_env_vars = ["MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM", "MAIL_PORT", "MAIL_SERVER"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Environment variable {var} is not set")

# Email server configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),  # Username for email server authentication
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),  # Password for email server authentication
    MAIL_FROM=os.getenv("MAIL_FROM"),  # Sender's email address
    MAIL_PORT=int(os.getenv("MAIL_PORT")),  # Email server port
    MAIL_SERVER=os.getenv("MAIL_SERVER"),  # Email server address
    MAIL_FROM_NAME="Maks",  # Name to display as the sender
    MAIL_STARTTLS=bool(int(os.getenv("MAIL_STARTTLS", 0))),  # Use STARTTLS if enabled
    MAIL_SSL_TLS=bool(int(os.getenv("MAIL_SSL_TLS", 1))),  # Use SSL/TLS if enabled
    USE_CREDENTIALS=True,  # Use authentication for the connection
    VALIDATE_CERTS=True,  # Validate SSL certificates
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',  # Path to the email templates folder
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    Sends a confirmation email with a verification link.

    :param email: Recipient's email address.
    :param username: User's name to display in the email.
    :param host: Base URL for the email confirmation.
    :raises ConnectionErrors: If there is an issue connecting to the email server.
    """
    try:
        # Create an email verification token
        token_verification = auth_services.create_email_token({"sub": email})

        # Construct the email message using a template
        message = MessageSchema(
            subject="Confirm your email",  # Email subject
            recipients=[email],  # Recipient email addresses
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html  # HTML format
        )

        # Initialize FastMail with the connection configuration
        fm = FastMail(conf)

        # Send the email using the specified template
        await fm.send_message(message, template_name="email.html")
        logger.info(f"Verification email sent to {email}")

    except ConnectionErrors as err:
        # Log connection errors
        logger.error(f"Failed to send email to {email}: {err}")
        raise HTTPException(status_code=500, detail="Failed to send email, please try again later.")

    except Exception as e:
        # Log any other exceptions
        logger.error(f"An error occurred while sending email to {email}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while sending the email.")
