import os

def get_db_path():
    if os.environ.get("role") == "manger":
        db_path = "/boil/manager/scripts/boilest.db"
    else:
        db_path = 'boilest.db'
    return db_path