# product-microservice

This is a Python-based microservice built using FastAPI that allows users to manage a product catalogue
and automatically update product prices from an external offer service (provided by Applifting).
It provides REST APIs for product management (CRUD) and an endpoint for retrieving offers related to the products.
Additionally, the service is designed to periodically update product offers
and automatically handle token-based authentication to the offer service.

## Features

- CRUD API: Create, read, update, and delete products in the catalogue.
- Automatic Price Updates: Periodically query the offers microservice for price updates and stock availability.
- Read-only API for Offers: Allows users to retrieve product offers, including their prices and stock levels.
- Swagger and Redoc Documentation: API documentation is automatically generated and available.

## Environment Setup

To run the microservice, you will need to create a `.env.prod` file (inside the project root folder)
with the following template:

```env
DATABASE_DRIVER=postgresql
DATABASE_HOST=db
DATABASE_NAME=microservice
DATABASE_PASSWORD=<your-password>
DATABASE_PORT=5432
DATABASE_USER=microservice
OFFERS_SERVICE_BASE_URL=https://python.exercise.applifting.cz
OFFERS_SERVICE_FETCH_PERIOD_SECONDS=60
OFFERS_SERVICE_REFRESH_TOKEN=<your-token>
```

and fill confidential information like `<your-password>` and `<your-token>`.

These variables are essential for:
- PostgreSQL: Internal data storage for products and offers.
- Authentication: Authenticating with the external offer service to fetch product offers.

## Running the Service

The application is containerized using Docker and managed by Docker Compose. To run the service:
- Ensure that Docker and Docker Compose are installed.
- Create the `.env.prod` file as specified above.
- Use the following command to build and run the containerized application (from the project root folder):

```bash
docker compose --env-file .env.prod up --build
```

The service will start and be accessible at http://localhost:8080.

## API Documentation

Once the application is running, you can access the API documentation at:
- Swagger: http://localhost:8080/docs
- Redoc: http://localhost:8080/redoc

These pages will provide a detailed overview of the available endpoints and how to interact with them.
Certain endpoints require to use basic authentication where the username can't be the same as user password. Thus,
you don't need to create any account beforehand.

## Contact

For any questions or support, feel free to contact [me](mailto:svabikfilip@gmail.com).
