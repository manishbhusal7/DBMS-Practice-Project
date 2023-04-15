import pathlib
from datetime import date
from typing import Optional, List  # 

from sqlmodel import Field, SQLModel, create_engine, Column, Integer, ForeignKey, Session

TOP_DIR = pathlib.Path(__file__).parent

# Database connection goes here
sqlite_file_name =  TOP_DIR / 'database' / 'database.db'
sqlite_url = f"sqlite:///{sqlite_file_name}"  # 
engine = create_engine(sqlite_url, echo=False)  # 

# This is needed to enforce foreign key constraints
# You can ignore this
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlite3 import Connection as SQLite3Connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

### Model Definitions ###
class User(SQLModel, table=True):  # 
    id: Optional[int] = Field(default=None, primary_key=True)  # this will autoincrement by default
    first_name: str
    last_name: str 

class Worklist(SQLModel, table=True):  # 
    id: Optional[int] = Field(default=None, primary_key=True)  # 
    user_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    )
    name: str
    date_created: str

class Task(SQLModel, table=True):  # 
    id: Optional[int] = Field(default=None, primary_key=True)  # 
    worklist_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("worklist.id", ondelete="CASCADE"))  
    )
    task: str
    date_created: str
    completed: bool

### Function Definitions ###
def create_user(first_name:str, last_name:str, save=True):
    user = User(first_name=first_name, last_name=last_name)
    if save:
        with Session(engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
    return user

def create_worklist(name:str, date_created:str=None, user_id:Optional[int]=None, save=True):
    if date_created is None:
        date_created = str(date.today())
    worklist = Worklist(name=name, date_created=date_created, user_id=user_id)
    if save:
        with Session(engine) as session:
            session.add(worklist)
            session.commit()
            session.refresh(worklist)

    return worklist

def create_task(task:str, date_created:str=None, completed:bool=False, worklist_id:Optional[int]=None, save=True):
    if date_created is None:
        date_created = str(date.today())
    
    task = Task(task=task, date_created=date_created, completed=completed, worklist_id=worklist_id)
    if save:
        with Session(engine) as session:
            session.add(task)
            session.commit()
            session.refresh(task)

    return task

def delete_item(item):
    with Session(engine) as session:
        session.delete(item)
        session.commit()

def get_users() -> List[User]:
    with Session(engine) as session:
        return list(session.query(User).all())
    
def get_worklists(user_id=1):
    with Session(engine) as session:
        return list(session.query(Worklist).where(Worklist.user_id == user_id))
    
def get_tasks(worklist_id=1):
    with Session(engine) as session:
        return list(session.query(Task).where(Task.worklist_id == worklist_id))
    
def update_entity(entity):
    with Session(engine) as session:
        session.add(entity)
        session.commit()
        session.refresh(entity)
    return entity

def delete_entity(entity):
    with Session(engine) as session:
        session.delete(entity)
        session.commit()

def create_fake_data():
    user_1 = create_user("Jeremy", "Castagno")
    worklist_1 = create_worklist("Priority", user_id=user_1.id)
    create_task("Get eggs", worklist_id=worklist_1.id)
    create_task("Get protein powder", worklist_id=worklist_1.id)

def create_db_and_tables():  # 
    """This creates our tables and add some fake data"""
    SQLModel.metadata.drop_all(engine)  # 
    SQLModel.metadata.create_all(engine)  # 
    create_fake_data()

# Create tables and fake data by: python -m todolist.db
if __name__ == "__main__":  # 
    create_db_and_tables()  # 
