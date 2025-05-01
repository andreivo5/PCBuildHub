# PCBuildHub

PCBuildHub is a full-stack Django web application that helps users plan and build custom PCs based on their performance needs and budget. Users can manually create a build or use the Smart Build feature, which recommends components using a combination of machine learning and rule-based logic. The platform also includes real-time pricing, compatibility checking, and user account features for saving and managing builds.

## Features

- Manual PC build creation with compatibility checks
- Smart Build recommendation engine for gaming, editing, and development
- Power draw estimation with PSU warnings
- Price tracking via custom web scraping scripts
- Component list views with search, filters, and details
- User accounts with saved builds and editable profiles
- Responsive frontend built using Bootstrap, HTML, CSS, and JavaScript

## Project Structure

The project is divided into modular Django apps, each handling a specific part of the platform:

### `builder/`
Handles build creation, editing, and validation.
- PCBuild model and views
- Compatibility checking logic
- Power usage calculation

### `components/`
Manages all hardware components and their data.
- Models for CPU, GPU, RAM, etc.
- CSV loading via `load.py`
- Filtering, sorting, and detail views

### `smartbuilder/`
Implements the Smart Build feature.
- LightGBM model integration
- Synergy prediction for CPU/GPU combos
- Rule-based selection for remaining components
- Budget recovery fallback system

### `login/`
Manages user accounts and authentication.
- Login, registration, logout
- User profile and saved builds

### `main/`
Handles general site views and layout.
- Homepage
- Shared templates and navbar

### `prices/, upgrade/`
Work in progress

### `ml/, scraping/`
Code that was run outside of the project folder to generate ML models and to scrape component prices.

## Deployment

- Uses PostgreSQL for local and production environments
- Deployed on a DigitalOcean droplet with Gunicorn and Nginx
- Environment variables managed through `.env` files
- Scraping and model training handled through internal scripts

## License

This project was developed as part of an academic final year submission. Not intended for commercial use.
