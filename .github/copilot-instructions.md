<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Motorcycle World - Django E-commerce Project

## Project Overview
This is a Django-based e-commerce platform for motorcycle accessories with a REST API architecture. The project uses Django REST Framework for API endpoints, JWT authentication, MariaDB database, and integrates OpenAI for AI-powered review summaries.

## Architecture Guidelines

### Backend Structure
- **API-First Design**: All business logic exposed via REST API endpoints
- **Modular Apps**: Separate Django apps for users, products, orders, and reviews
- **Service Layer**: Business logic separated into services/ directory
- **Custom User Model**: Extended User model with role-based permissions (admin/customer)

### Database Design
- **Normalized Schema**: Properly normalized with explicit foreign keys
- **No Direct M2M**: All many-to-many relationships use through tables
- **MariaDB/MySQL**: Primary database with connection on port 3310

### Authentication & Security
- **JWT Tokens**: Using Simple JWT for authentication
- **Role-Based Access**: Admin and Customer roles with appropriate permissions
- **API Security**: Proper validation and permission checks

### Frontend Integration
- **Template + API**: Django templates consume internal REST API
- **Tailwind CSS**: Responsive design with utility-first CSS
- **JavaScript**: Vanilla JS for dynamic interactions and API calls

## Development Standards

### Code Organization
- Models in respective app/models.py
- API views using DRF ViewSets and generics
- Serializers for data validation and transformation
- URL patterns organized by app with api/ prefix
- Business logic in services/ layer

### Database Connection
```python
# Current database configuration
DB_HOST = '127.0.0.1'
DB_PORT = 3310
DB_USER = 'root'
DB_PASSWORD = 'TadsDb'
DB_NAME = 'Test_Final'
```

### API Patterns
- RESTful endpoints with proper HTTP methods
- Consistent response format with DRF
- Pagination for list endpoints
- Filtering and search capabilities
- Proper error handling and validation

### Key Features to Maintain
1. **Product Management**: Categories, products, variants, images
2. **Shopping Cart**: Session-based cart with API endpoints
3. **Order Processing**: Complete order workflow with status tracking
4. **Review System**: Customer reviews with AI-generated summaries
5. **User Management**: Registration, authentication, profile management

## AI Integration
- OpenAI API for review summaries
- Fallback mechanisms when AI is unavailable
- Sentiment analysis of customer reviews
- Environment variable for API key configuration

## Coding Preferences
- Use class-based views for consistency
- Implement proper serializer validation
- Include docstrings for complex functions
- Follow Django/DRF best practices
- Use type hints where appropriate
- Implement proper error handling
