from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import contacts, auth, users
from typing import Dict
import os

# Load environment variables from the .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="My Application",
    description="This is an API for managing contacts, authentication, and users.",
    version="1.0.0",
)

# CORS configuration based on environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")  # Read from environment or allow all

# Setup CORS (Cross-Origin Resource Sharing) for the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Use environment variable for origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers for different parts of the application (contacts, auth, users)
app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify if the server is running.

    :return: Dictionary with a status message.
    :rtype: Dict[str, str]
    """
    return {"status": "ok"}


@app.get("/", tags=["Root"])
def read_root() -> Dict[str, str]:
    """
    Root endpoint to check if the server is up and running.

    :return: Dictionary with a welcome message.
    :rtype: Dict[str, str]
    """
    return {"message": "Hello World"}


# Global exception handler (optional)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler to catch and handle all unhandled exceptions.

    :param request: The request object.
    :param exc: The raised exception.
    :return: JSON response with error message.
    """
    return {"error": "An unexpected error occurred. Please try again later."}
