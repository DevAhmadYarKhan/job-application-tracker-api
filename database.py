from sqlmodel import Session, SQLModel, create_engine

database_url = "sqlite:///database.db"

engine = create_engine(database_url, connect_args={"check_same_thread": False},)

# Function that creates the database itself
def create_db():
    SQLModel.metadata.create_all(engine)

# Gives a session that allows for interacting with the database, we inject it into our routes
def get_session():
    with Session(engine) as session:
        yield session