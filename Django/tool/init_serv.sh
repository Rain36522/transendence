
echo "Preparing django server"
python3 manage.py migrate
echo "Start django server"
python3 manage.py runserver 0.0.0.0:8000
