# Start Backend Locally

Open a terminal and navigate to the `backend` directory:
```bash
cd ~/Desktop/Projects/CareerScoper/backend
```

Create and activate a virtual environment (only needed once):
```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the Django server:
```bash
python manage.py runserver 0.0.0.0:8000
```
This service will run on **Port 8000**.
