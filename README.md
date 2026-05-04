# NewsApp — Django Capstone Project

A news application where journalists submit articles, editors approve them,
subscribers receive email notifications, and readers can subscribe to
publishers and journalists.

## Setup & Running

### 1. Clone the repository
```bash
git clone https://github.com/YerimahYD/news_app.git
cd news_app
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv myenv
source myenv/bin/activate      # macOS/Linux
myenv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create the MariaDB database
Open the MySQL/MariaDB CLI or HeidiSQL and run:
```sql
mysql -u root -p
CREATE DATABASE news_app_db CHARACTER SET utf8mb4;
EXIT;
```

### 5. Update database credentials in settings.py
Open `config/settings.py` and update:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'news_app_db',
        'USER': 'your_actual_username',
        'PASSWORD': 'your_actual_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 6. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser (for admin panel)
```bash
python manage.py createsuperuser
```

### 8. Run linting
```bash
flake8 .
black .
```

### 9. Run tests
```bash
python manage.py test news -v 2
```

### 10. Start the development server
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000 in your browser.

## Roles & Permissions

| Role       | Articles                         | Newsletters              |
|------------|----------------------------------|--------------------------|
| Reader     | View approved only               | View (approved only)     |
| Journalist | Create, view, edit/delete (own)  | Create, view, edit       |
| Editor     | View, update, delete all; approve| View, update, delete     |

## Publisher Registration Flow

1. A publication registers at `/publishers/register/`
2. Journalists and editors select the publisher during their own registration
3. Readers can subscribe to publishers at `/publishers/`
4. When an editor approves an article, all subscribers are emailed automatically

## REST API Endpoints

| Method | Endpoint                      | Access                    |
|--------|-------------------------------|---------------------------|
| POST   | /api/token/                   | Anyone (obtain token)     |
| GET    | /api/articles/                | Authenticated             |
| POST   | /api/articles/                | Journalists only          |
| GET    | /api/articles/subscribed/     | Authenticated             |
| GET    | /api/articles/<id>/           | Authenticated             |
| PUT    | /api/articles/<id>/           | Journalist (own)/Editor   |
| DELETE | /api/articles/<id>/           | Journalist (own)/Editor   |
| GET    | /api/approved/                | Authenticated             |
| POST   | /api/approved/                | Authenticated (internal)  |
| GET    | /api/newsletters/             | Authenticated             |
| POST   | /api/newsletters/             | Journalists only          |

## Running with Docker

### Step 1 — Make sure Docker Desktop is running
Open Docker Desktop and wait for it to fully start.

### Step 2 — Build the Docker image
```bash
docker build -t news-app .
```

### Step 3 — Run the container
```bash
docker run -d -p 8000:8000 news-app
```

### Step 4 — Visit the app
Open your browser and go to **http://localhost:8000**

### Step 5 — Stop the container
```bash
docker ps                    # get container ID
docker stop [container_id]   # stop the container
```

### Step 6 — Using Docker Compose
```bash
docker-compose up    # start
docker-compose down  # stop
```