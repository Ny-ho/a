import asyncio
from datetime import datetime,timedelta
from app.database import engine#sqlite database connection engine
from sqlmodel.ext.asyncio.session import AsyncSession#create async database sessions
from app.borrows.schemas import BorrowCreate#schema object expecting userid,bookid,duedate
from app.borrows.service import BorrowService#import borrowservice class that contains atomic borrow_book
from app.books.models import Book
from sqlmodel import select
#both allows us to query book table

async def simulate_user_borrow(user_name:str,user_id:int,book_id:int):
    async with AsyncSession(engine) as session:#opens a independent seperate databse session for 2 seperate users
        borrow_data=BorrowCreate(
            user_id=user_id,
            book_id=book_id,
            due_date=datetime.utcnow() + timedelta(days=14)
        )#constructs request payload with userid,bookid and 14 day due date

        try:
            print(f"{user_name}is attempting to borrow {book_id}...")
            result=await BorrowService.borrow_book(session,borrow_data)
            print(f"success:{user_name}succesfully borrowed book! record id:{result.id}")
            return result
        except Exception as e:
            print(f"failed:{user_name}got an error:{e}")
            return e
        #in borrowbook if atomic UPDATE succeeds , it prints SUCCESS

async def main():
        #find an available book in the database
        async with AsyncSession(engine) as session:
            statement=select(Book).where(Book.status=="available")
            book=(await session.exec(statement)).first()

            if not book:
                print("no available book found in database to test with")
                return
            print(f"testing concurrency on book id {book.id}:'{book.title}'\n")
            book_id=book.id

    #Fire BOTH requests at the same time
        results=await asyncio.gather(
            simulate_user_borrow("Alice",1,book_id),
            simulate_user_borrow("BOB",2,book_id),
            return_exceptions=True
    )#asyncio.gather puts the coroutine into eventloop at the exact same millisecond
if __name__ == "__main__":
    asyncio.run(main())