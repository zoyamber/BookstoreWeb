from db import db
from app import app
from models import Book, Category, User, BookRental
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.sql import func
from random import random, randint
import csv
import sys
from sqlalchemy import select

def create_tables():
    with app.app_context():
        db.create_all()

def drop_tables():
    with app.app_context():
        db.drop_all()

def create_rentals():
    now = datetime.now()
    with app.app_context():
        for _ in range(10):
            user = db.session.execute(select(User).order_by(func.random())).scalar()
            book = db.session.execute(select(Book).order_by(func.random())).scalar()
            rented = now - timedelta(days=randint(10, 25), hours=randint(0, 5))
            returned = random() > 0.5
            if returned:
                returned = rented + timedelta(days=randint(2, 9), hours=randint(0, 100), minutes=(randint(0, 100)))
            else:
                returned = None

            rental = BookRental(user=user, book=book, rented=rented, returned=returned)
            db.session.add(rental)
            db.session.commit()

def get_category_by_name(name):
    with app.app_context():
        statement = select(Category).where(Category.name == name)
        possible = db.session.execute(statement).scalar()
        return possible

def get_or_create_category(name):
    possible = get_category_by_name(name)

    if possible:
        return possible
    category = Category(name=name)
    with app.app_context():
        db.session.add(category)
    return category

def load_data_from_csv(filename):
    with open(filename, "r") as fp:
        reader = csv.DictReader(fp)
        if "books" in filename:
            for row in reader:
                category = row.pop("category")
                row["category"] = get_or_create_category(category)
                book = Book(**row)
                with app.app_context():
                    db.session.add(book)
                    db.session.commit()
        if "users" in filename:
            for row in reader:
                user = User(**row)
                with app.app_context():
                    db.session.add(user)
                    db.session.commit()

def import_tables():
    load_data_from_csv("data/books.csv")
    load_data_from_csv("data/users.csv")

def import_bookrentals():
    with app.app_context():
        with open("./data/bookrentals.csv", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for rental in reader:
                user_statement = select(User).where(User.name == rental["user_name"])
                user = db.session.execute(user_statement).scalar()
                book_statement = select(Book).where(Book.upc == rental["book_upc"])
                book = db.session.execute(book_statement).scalar()

                if user and book:
                    rented_on = datetime.strptime(rental["rented"], "%Y-%m-%d %H:%M")
                    returned_on = datetime.strptime(rental["returned"], "%Y-%m-%d %H:%M") if rental["returned"] else None
                    book_rental = BookRental(user=user, book=book, rented_on=rented_on, returned_on=returned_on)
                    db.session.add(book_rental)
                    db.session.commit()
                else:
                    if not user:
                        print(f"User not found: {rental['user_name']}")
                    if not book:
                        print(f"Book not found: {rental['book_upc']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            drop_tables()
            create_tables()
        if sys.argv[1] == "import":
            import_tables()
        if sys.argv[1] == "rentals":
            create_rentals()
