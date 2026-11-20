# fullstack_developer_capstone

## National Car Dealership Review Portal

A central web portal for a national car dealership with local branches spread across the United States. This application enables customers to look up dealership branches by state, view customer reviews and sentiment analysis, create user accounts, and post their own reviews.

### Features
- **Anonymous Users**: View static pages (Home, About Us, Contact Us), browse dealerships, filter branches by state, and view dealer reviews.
- **Authorized Users**: Authenticate, register, and write reviews with purchase details and ratings.
- **Admin Users**: Manage car makes, models, and dealer attributes through Django Admin.
- **Microservices Architecture**:
  - Django application with SQLite for car makes, models, and user authentication.
  - Express.js and MongoDB microservice running in Docker for managing dealerships and customer reviews.
  - IBM Code Engine Sentiment Analyzer service for review sentiment evaluation.
  - React frontend components for dynamic user management and reviews.
  - CI/CD automated linting workflow with GitHub Actions and container deployment.
