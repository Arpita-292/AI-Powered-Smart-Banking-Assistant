import sqlite3
import sys
import os

DB_NAME = os.path.join(
    os.path.dirname(__file__),
    "siri_bank.db"
)


def reset_customer_bank_account(customer_id):

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    try:

        # ----------------------------------------------------
        # FIND CUSTOMER
        # ----------------------------------------------------

        user = conn.execute(
            """
            SELECT id, customer_id, full_name, phone_number
            FROM users
            WHERE customer_id = ?
            """,
            (customer_id,)
        ).fetchone()

        if not user:

            print(
                f"\nCustomer {customer_id} was not found."
            )

            return


        user_id = user["id"]

        print("\n----------------------------------------")
        print(" SIRI BANK TEST ACCOUNT RESET")
        print("----------------------------------------")

        print(
            f"Customer ID : {user['customer_id']}"
        )

        print(
            f"Name        : {user['full_name']}"
        )

        print(
            f"Mobile      : {user['phone_number']}"
        )


        # ----------------------------------------------------
        # SHOW EXISTING ACCOUNT
        # ----------------------------------------------------

        accounts = conn.execute(
            """
            SELECT id, account_number, balance, status
            FROM accounts
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchall()


        if not accounts:

            print(
                "\nThis customer already has NO bank account."
            )

            print(
                "You can directly test the Savings Account request."
            )

            return


        print("\nExisting bank account(s):")

        for account in accounts:

            print(
                f"  Account Number : "
                f"{account['account_number']}"
            )

            print(
                f"  Balance        : "
                f"₹{account['balance']}"
            )

            print(
                f"  Status         : "
                f"{account['status']}"
            )


        # ----------------------------------------------------
        # CONFIRM
        # ----------------------------------------------------

        confirmation = input(
            "\nType RESET to remove this customer's "
            "bank account: "
        ).strip()


        if confirmation != "RESET":

            print(
                "\nReset cancelled."
            )

            return


        # ----------------------------------------------------
        # REMOVE TRANSACTIONS
        # ----------------------------------------------------

        conn.execute(
            """
            DELETE FROM transactions
            WHERE sender_id = ?
               OR receiver_id = ?
            """,
            (
                user_id,
                user_id
            )
        )


        # ----------------------------------------------------
        # REMOVE ACCOUNT
        # ----------------------------------------------------

        conn.execute(
            """
            DELETE FROM accounts
            WHERE user_id = ?
            """,
            (user_id,)
        )


        # ----------------------------------------------------
        # REMOVE OLD SAVINGS ACCOUNT REQUESTS
        # ----------------------------------------------------

        conn.execute(
            """
            DELETE FROM requests
            WHERE user_id = ?
              AND request_type = 'SAVINGS_ACCOUNT'
            """,
            (user_id,)
        )


        # ----------------------------------------------------
        # REMOVE OLD ACCOUNT CREATION NOTIFICATIONS
        # ----------------------------------------------------

        conn.execute(
            """
            DELETE FROM notifications
            WHERE user_id = ?
              AND (
                    title LIKE '%Account%'
                    OR title LIKE '%account%'
                  )
            """,
            (user_id,)
        )


        conn.commit()


        print("\n========================================")
        print(" RESET SUCCESSFUL")
        print("========================================")

        print(
            f"Customer ID : {user['customer_id']}"
        )

        print(
            f"Customer    : {user['full_name']}"
        )

        print(
            "\nApp access : ACTIVE"
        )

        print(
            "Bank account : NOT CREATED"
        )

        print(
            "\nYou can now log in and test:"
        )

        print(
            "Savings Account → Submit Request"
        )

        print(
            "→ Admin Approval"
        )

        print(
            "→ Account Creation"
        )

        print(
            "→ Customer Notification"
        )

        print(
            "========================================\n"
        )


    except Exception as e:

        conn.rollback()

        print(
            "\nERROR:"
        )

        print(e)


    finally:

        conn.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\nSIRI BANK - TEST ACCOUNT RESET")

    customer_id = input(
        "Enter the Customer ID to reset "
        "(example: CUST1005): "
    ).strip().upper()

    if not customer_id:

        print(
            "Customer ID is required."
        )

        sys.exit()


    reset_customer_bank_account(
        customer_id
    )