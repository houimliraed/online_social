from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from typing import Optional
from app.schemas import PostCreate,PostResponse
from app.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
import shutil
import tempfile
import os
import uuid
from app.users import current_active_user, AuthenticationBackend, FastAPIUsers, UserCreate, UserRead, UserUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(
    FastAPIUsers.get_auth_router(AuthenticationBackend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    FastAPIUsers.get_register_router(user_schema=UserRead, user_create_schema=UserCreate), prefix="/auth", tags=["auth"]
)
app.include_router(
    FastAPIUsers.get_users_router(user_schema=UserRead, user_update_schema=UserUpdate), prefix="/users", tags=["users"], dependencies=[Depends(current_active_user)]
)

@app.post('/upload_file')
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    try:
        _, ext = os.path.splitext(file.filename or "")
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        
        new_filename = f"{uuid.uuid4().hex}{ext}"
        final_path = os.path.join(uploads_dir, new_filename)
        shutil.move(temp_file_path, final_path)
        temp_file_path = final_path  

      
        url = f"/uploads/{new_filename}"  
        file_type = ext.lstrip(".").lower() or "bin"
        file_name = file.filename or new_filename

    except Exception as e:
       
        raise HTTPException(status_code=500, detail=f"file upload failed: {e}")
    finally:
       
        try:
            if temp_file_path and os.path.exists(temp_file_path):

                pass
        finally:
            try:
                file.file.close()
            except Exception:
                pass

    post = Post(
        caption = caption,
        url = url,
        file_type = file_type,
        file_name = file_name
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post

@app.get('/feed')
async def get_feed(
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()
    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id": str(post.id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat()
                
            }
        )
    return {"posts": posts_data}

@app.delete('/post/{post_id}')
async def delete_post(post_id: str, session: AsyncSession = Depends(get_async_session)):
    try:
        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        await session.delete(post)
        await session.commit()
        return {"detail": "Post deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    

