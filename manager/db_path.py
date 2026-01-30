import os

def get_db_path():
    if os.environ.get("Role") == "Manger":
        db_path = "/Boil/App/boilest.db"
    else:
        db_path = 'boilest.db'
    return db_path