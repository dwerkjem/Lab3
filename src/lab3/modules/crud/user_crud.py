import questionary
from .database import Database
from .crud import CRUD

db = Database()

def edit_customer(customer_id: str, customer_name: str):
    customer_name = questionary.text(
        "What would you like to change the name to?",
        default=customer_name
    ).ask()

    db.cursor.execute(
        """
        UPDATE customers
        SET full_name = ?
        WHERE customer_id = ?
        """,
        (
            customer_name,
            customer_id,
        ),
    )

    db.commit()