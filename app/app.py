
from fastapi import FastAPI, HTTPException
from typing import Optional
from app.schemas import PostCreate,PostResponse



app = FastAPI()


# first endpoint
@app.get('/')
def root():
    return{
        "hello": "world"
    }
