# Django REST API - Rock of Ages

## Notes

There are no views, models, or serializers in this boilerplate project. The only code that is included is the ability to register and login. The `urls.py` file already imports the required functions from `views/auth.py`.

## Getting Started

1. Clone this repository and `cd` to the project directory
2. Run `pipenv shell`
3. Run `pipenv install`
4. Run `python3 manage.py migrate` to create the default Django tables in your database
5. Open the project directory in VS Code
6. Press <kbd>⌘</kbd><kbd>SHIFT</kbd><kbd>P</kbd> (Mac), or <kbd>Ctrl</kbd><kbd>SHIFT</kbd><kbd>P</kbd> (Windows) to open the Command Palette, and select "Python: Select Interpreter".
4. Search for "rock" and select the interpreter that starts with those characters. There should only be one to choose from.
7. Start the debugger
   1. Mac: **Shift+Option+D**
   2. Windows: **Shift+Alt+D**
8. Verify that the process starts with no exceptions
9. Open Postman and create a POST request to http://localhost:8000/register with the following JSON body and verify that you can create a new user and get a token in the response body -
   ```json
   {
      "email": "admina@straytor.com",
      "password": "straytor",
      "first_name": "Admina",
      "last_name": "Straytor"
   }
   ```

## How This Was Generated

1. `mkdir rockproject`
2. `cd rockproject`
3. `pipenv shell`
4. `pipenv install django autopep8 pylint djangorestframework django-cors-headers pylint-django`
5. `django-admin startproject rockproject .`
6. `python3 manage.py startapp rockapi`

You would follow the same process for building any Django REST API project. Then take the following code from this project.

1. `rockproject/settings.py` and replace every instance `rockapi` and `rockproject` with your names.
2. `rockproject/urls.py` and replace `rockapi` with your app name.
3. `rockapi/views/auth.py`
4. `rockapi/views/__init__.py`
5. The `.vscode` directory and its contents. Replace `rockproject` in the settings file with your project name.
6. The `.pylintrc` file.

## Running Tests
1. Run `pipenv shell`
2. Run `pipenv install`
3. Run `python manage.py test`
