Project Name

# Bricolage Express - Guide d'utilisation rapide

## Application Web

Configuration
Environment Variables
You need to configure the following environment variables in the .env file:

FLASK_SECRET_KEY: A secure random secret key for Flask.
DATABASE_URL: Path to the database (SQLite).
MAIL_SERVER: SMTP server (e.g., smtp.gmail.com).
MAIL_PORT: Mail server port (587 for Gmail).
MAIL_USE_TLS: Use TLS encryption for mail.
MAIL_USERNAME: Your email username.
MAIL_PASSWORD: Your email app password.
ADMIN_EMAIL: Admin email for managing the project.

## Fonctionnalités principales

- 🔍 Recherche de produits
- 📁 Filtrage par catégorie
- 🛒 Gestion du panier
- ⚙️ Administration des produits


License
This project is licensed under the MIT License. See LICENSE for more details.

Features
User authentication and management.
Database integration with SQLite.
Email notifications using Gmail SMTP.
Secure environment variable management with .env.

Technologies Used
Back-End: Flask, Python
Database: SQLite
Email Service: Gmail SMTP
Environment Management: .env for environment variables
Hosting/Development: Local development mode with Flask



