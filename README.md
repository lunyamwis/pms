# Real Estate Management System

A comprehensive real estate management system built with Django, featuring property listings, user management, and agent interactions.

## Features

- User Authentication and Authorization
- Property Listings with Advanced Search
- Agent Profiles and Dashboard
- User Dashboard
- Property Image Management
- Messaging System
- Advanced Search and Filtering
- Responsive Modern UI

## Tech Stack

- Django 5.0.2
- PostgreSQL
- Bootstrap 5
- Django REST Framework
- Django Allauth for Authentication
- CKEditor for Rich Text Editing

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd realestate
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file and set environment variables:
```bash
cp .env.example .env
# Edit .env file with your settings
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run development server:
```bash
python manage.py runserver
```

## Project Structure

```
realestate/
├── manage.py
├── core/
├── accounts/
├── properties/
├── agents/
├── messaging/
└── static/
    ├── css/
    ├── js/
    └── img/
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 