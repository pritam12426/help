# HELP

make a .env file and add the apt key of gemini

``` env
KEY = "#*#*#*#*#*#*#*#*#*#*#*#"
```

make a env

``` sh
touch .env
python3 -m venv venv
source venv/bin/activate
pip install google-generativeai=0.8.5
python ./main.py
```
