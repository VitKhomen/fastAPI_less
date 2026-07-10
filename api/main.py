import uvicorn
from fastapi import FastAPI
from api.routers import users, product, auth


app = FastAPI(
    title="FastAPI lessons",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(product.router)
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
