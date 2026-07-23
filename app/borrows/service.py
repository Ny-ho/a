#Database ACID Concurrency Control
# implemented atomic UPDATE queries combined with database write-serialization to guarantee thread-safe book borrowing, preventing double-borrow race conditions when concurrent requests hit the API simultaneously.
from app.users.models import User
from sqlalchemy.engine import result
from sqlalchemy.ext.asyncio import session
from datetime import datetime
from sqlmodel import select
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel.ext.asyncio.session import AsyncSession
from app.borrows.models import BorrowRecord
from app.borrows.schemas import BorrowResponse,BorrowCreate
from app.books.models import Book

class BorrowService:
    @staticmethod 
    async def get_all_borrows(session:AsyncSession):
        statement=select(BorrowRecord)
        return (await session.exec(statement)).all()
    @staticmethod
    async def get_borrow_by_id(session:AsyncSession,borrow_id:int):
        return await session.get(BorrowRecord,borrow_id)
#what if 2 users borrow the last book at a same time . they both get "borowwed" which is wrong
#ok so previously we coulnt lock read and thus both see available and both update or one overwrite other.so now instead of read or select the available book if "available , we write all inside write so on two can join or enter at same time . 
#Atomicity of ACID
    @staticmethod
    async def borrow_book(session:AsyncSession,borrow_data:BorrowCreate):
        from sqlalchemy import text
        from fastapi import HTTPException,status

        
        book=await session.get(Book,borrow_data.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with ID {borrow_data.book_id} not found"
            )
        statement=text("UPDATE book SET status='borrowed' WHERE id =:book_id AND status ='available' ")
        result=await session.execute(statement,{"book_id":borrow_data.book_id})

        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Book '{book.title}'is not available or already borrowed")
        db_borrow=BorrowRecord(**borrow_data.model_dump())
        session.add(db_borrow)

        await session.commit()
        await session.refresh(db_borrow)
        return db_borrow

    @staticmethod
    async def return_book(session:AsyncSession,db_borrow:BorrowRecord):
        db_borrow.return_date=datetime.utcnow()
        session.add(db_borrow)
        book=await session.get(Book,db_borrow.book_id)
        if book:
            book.status="available"
            session.add(book)
        await session.commit()
        await session.refresh(db_borrow)
        return db_borrow
