from app.database import engine
from app.models import Base

Base.metadata.create_all(engine)

print("Toutes les tables ORM sont créées.")