from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

import schemas
from src.database.session import get_db
from src.database.models import MovieModel


router = APIRouter()

@router.get("/movies/{movie_id}/", response_model=schemas.movies.MovieDetailResponseSchema)
async def get_film(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.get("/movies/", response_model=schemas.movies.MovieListResponseSchema)
async def get_film(request: Request, page: int = Query(default=1, ge=1), per_page: int = Query(default=10, ge=1, le=20), db: AsyncSession = Depends(get_db)):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_items = total_items or 0

    movies = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    movies = list(movies.scalars().all())

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_pages = (total_items + per_page - 1) // per_page
    page_url = request.url.path

    return schemas.movies.MovieListResponseSchema(
        movies=movies,
        prev_page=(
            f"{page_url}?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        next_page=(
            f"{page_url}?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )
