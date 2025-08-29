# SQLAlchemy ORM Fundamentals

## Key Characteristics
- Builds on SQLAlchemy Core to provide object-relational mapping
- Allows mapping Python classes to database tables
- Provides an object persistence mechanism called "Session"
- Extends Core SQL Expression Language to work with user-defined objects

## Model Declaration
- Use `DeclarativeBase` as a base class for ORM models
- Define tables using `__tablename__`
- Use type annotations with `Mapped` and `mapped_column()`
- Specify primary keys and relationships

Example:
```python
class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
```

## Engine Creation
- Create database connection using `create_engine()`
- Supports multiple databases (SQLite used in example)
- Configure with parameters like `echo=True` for logging

## Table Creation
- Use `Base.metadata.create_all(engine)` to generate database schema
- Automatically creates tables based on model definitions

## Session and Data Persistence
- Use `Session` for database interactions
- Add objects with `session.add_all()`
- Commit transactions with `session.commit()`

## Querying
- Use `select()` function to create queries
- Apply filters with `.where()` method
- Execute with `session.scalars()`

## CRUD Operations
- Create: Instantiate model objects and add to session
- Read: Use `select()` with various filtering options
- Update: Modify object attributes
- Delete: Use `session.delete()` or remove related objects

## Core Concepts
- SQLAlchemy is presented as two distinct APIs: Core and ORM
- Core provides foundational database toolkit functionality
- ORM adds object mapping and persistence layer