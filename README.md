# FastAPI Contacts and User Management API

This project is a FastAPI-based application that provides functionality for managing contacts, user authentication, email verification, and rate limiting. It uses PostgreSQL as the database, Redis for rate limiting, and Cloudinary for handling avatar uploads. Additionally, the project is configured for email verification and JWT authentication.

## Features

- **User Registration**: Sign up with an email, password, and username.
- **JWT Authentication**: Token-based authentication (access and refresh tokens).
- **Contact Management**: Create, update, delete, and search for contacts.
- **Rate Limiting**: Limit the number of requests per user using Redis.
- **Email Verification**: Send a confirmation email during registration using FastAPI-Mail.
- **Avatar Upload**: Upload user avatars to Cloudinary.
- **Health Check**: Basic health check route.

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Cache/Rate Limiter**: Redis
- **Email**: FastAPI-Mail, SMTP
- **Cloud Storage**: Cloudinary
- **Authentication**: JWT (JSON Web Tokens)
- **Testing**: Pytest, HTTPX, pytest-asyncio

## Prerequisites

To run this project locally, you need the following installed:

- **Python 3.12+**
- **Docker & Docker Compose**
- **Poetry** (for dependency management)
