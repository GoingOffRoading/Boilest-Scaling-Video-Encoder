import os

def get_db_path():
    if os.environ.get("Role") == "Manager":
        db_path = "/boil/app/boilest.db"
    else:
        db_path = 'boilest.db'
    return db_path