"""Affiche le SQL PostgreSQL des 8 tables à partir des modèles.  python -m database.schema.generer_sql"""
from sqlalchemy import Enum
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

import app.models  # noqa: F401
from app.db.base import Base

d = postgresql.dialect()
print("-- Schéma PostgreSQL généré à partir des modèles (app/models) : tables du diagramme de classes UML v2.")
print("-- Documentation uniquement : la base est créée par Alembic (`alembic upgrade head`), pas par ce fichier.")
print("-- Régénérer : python -m database.schema.generer_sql > database/schema/schema.sql\n")
enums = {c.type.name: c.type.enums for t in Base.metadata.sorted_tables for c in t.columns if isinstance(c.type, Enum)}
for nom, valeurs in enums.items():
    print(f"CREATE TYPE {nom} AS ENUM ({', '.join(repr(v) for v in valeurs)});")
print()
for t in Base.metadata.sorted_tables:
    print(str(CreateTable(t).compile(dialect=d)).strip() + ";")
    for i in sorted(t.indexes, key=lambda i: i.name):
        print(str(CreateIndex(i).compile(dialect=d)).strip() + ";")
    print()
