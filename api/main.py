
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.routers import users


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await create_tables()
#     print("✅ Database ready")
#     yield
#     print("🛑 Shutting down")


app = FastAPI(
    lifespan=lifespan,
    title="FastAPI lessons",
    version="1.0.0",
)

app.include_router(users.router)


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
