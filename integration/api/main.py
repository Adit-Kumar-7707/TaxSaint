"""TaxSaint API entry point."""


from fastapi import FastAPI
from sqlalchemy import inspect
from sqlalchemy import text
from database_manager.connection import engine

app = FastAPI(title="TaxSaint API")


@app.get("/")
def home():
    return {"message": "TaxSaint API is running"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(inspect(engine).dialect.statement_compiler(
                inspect(engine).dialect, None
            ).statement) if False else connection.exec_driver_sql("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }