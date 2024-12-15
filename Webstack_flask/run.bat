@echo off
echo Installation/mise a jour des dependances...
python -m pip install -r requirements.txt

echo Initialisation de la base de donnees...
python -c "from app import db; db.create_all()"

echo Démarrage de l'application Bricolage Express...
set FLASK_APP=app.py
set FLASK_ENV=development
python app.py
pause
