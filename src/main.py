import sqlite3
import datetime

def create_connection(db_file="library.db"):
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    
    # Table for library items (added status and location columns)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        item_type TEXT CHECK(item_type IN ('print_book', 'online_book', 'magazine', 'journal', 'cd', 'record')),
        author TEXT,
        publisher TEXT,
        publication_year INTEGER,
        ISBN TEXT UNIQUE CHECK (ISBN IS NULL OR LENGTH(ISBN) = 10 OR LENGTH(ISBN) = 13),
        available_copies INTEGER NOT NULL,
        status TEXT DEFAULT 'available' CHECK(status IN ('available','borrowed','donated')),
        location TEXT DEFAULT 'Library Shelf'
    );
    """)
    
    # Table for donations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Donations (
        donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        donation_date DATE DEFAULT (DATE('now')),
        condition TEXT,
        FOREIGN KEY(user_id) REFERENCES Personnel(personnel_id),
        FOREIGN KEY(item_id) REFERENCES Items(item_id)
    );
    """)
    
    # Table for borrow transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BorrowTransactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        borrow_date DATE NOT NULL,
        due_date DATE NOT NULL,
        return_date DATE,
        fine REAL DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES Personnel(personnel_id),
        FOREIGN KEY(item_id) REFERENCES Items(item_id)
    );
    """)
    
    # Trigger: Calculate fine if return_date is later than due_date
    cursor.execute("DROP TRIGGER IF EXISTS calculate_fine;")
    cursor.execute("""
    CREATE TRIGGER calculate_fine AFTER UPDATE OF return_date ON BorrowTransactions
    FOR EACH ROW
    WHEN NEW.return_date IS NOT NULL AND julianday(NEW.return_date) > julianday(NEW.due_date)
    BEGIN
        UPDATE BorrowTransactions
        SET fine = (julianday(NEW.return_date) - julianday(NEW.due_date)) * 1.0
        WHERE transaction_id = NEW.transaction_id;
    END;
    """)
    
    # Table for event rooms
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT NOT NULL,
        capacity INTEGER NOT NULL
    );
    """)
    
    # Table for events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        event_date DATE NOT NULL,
        event_time TEXT,
        recommended_audience TEXT CHECK(recommended_audience IN ('children', 'adults', 'both')),
        room_id INTEGER NOT NULL,
        FOREIGN KEY(room_id) REFERENCES Rooms(room_id)
    );
    """)
    
    # Table for event registrations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EventRegistrations (
        registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        registration_date DATE DEFAULT (DATE('now')),
        FOREIGN KEY(user_id) REFERENCES Personnel(personnel_id),
        FOREIGN KEY(event_id) REFERENCES Events(event_id)
    );
    """)
    
    # Trigger: Check event capacity before registration
    cursor.execute("DROP TRIGGER IF EXISTS check_event_capacity;")
    cursor.execute("""
    CREATE TRIGGER check_event_capacity BEFORE INSERT ON EventRegistrations
    FOR EACH ROW
    BEGIN
      SELECT CASE 
        WHEN ((SELECT COUNT(*) FROM EventRegistrations WHERE event_id = NEW.event_id) >= 
             (SELECT capacity FROM Rooms WHERE room_id = (SELECT room_id FROM Events WHERE event_id = NEW.event_id)))
        THEN RAISE(ABORT, 'Event capacity reached')
      END;
    END;
    """)
    
    # Table for personnel
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Personnel (
        personnel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        gender TEXT NOT NULL CHECK(gender IN ('M', 'F', 'Other')),
        birth_date DATE NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        role TEXT NOT NULL CHECK(role IN ('Member', 'Staff', 'Volunteer'))
    );
    """)

    # Addon-table for Staff
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Staffs (
        staff_id INTEGER PRIMARY KEY REFERENCES Personnel(personnel_id),
        position TEXT NOT NULL,
        salary REAL NOT NULL
    );
    """)

    # Addon-table for Volunteers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Volunteers (
        volunteer_id INTEGER PRIMARY KEY REFERENCES Personnel(personnel_id),
        participation_count INTEGER NOT NULL DEFAULT 0
    );
    """)
    
    # Table for volunteer registrations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS VolunteerRegistrations (
        v_registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES Personnel(personnel_id),
        FOREIGN KEY(event_id) REFERENCES Events(event_id)
    );
    """)
    
    # Trigger: Update volunteer participation count after registration
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_participation_count
        AFTER INSERT ON VolunteerRegistrations
        FOR EACH ROW
        BEGIN
            UPDATE Volunteers
            SET participation_count = participation_count + 1
            WHERE volunteer_id = NEW.user_id;
        END;
        """)
    
    # Table for help requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS HelpRequests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        librarian_id INTEGER,
        request_date DATE DEFAULT (DATE('now')),
        description TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(user_id) REFERENCES Personnel(personnel_id),
        FOREIGN KEY(librarian_id) REFERENCES Personnel(personnel_id)
    );
    """)
    
    conn.commit()

def populate_sample_data(conn):
    cursor = conn.cursor()
    
    # Insert sample rooms (at least 3 entries)
    rooms = [
        ("Main Hall", 50),
        ("Conference Room", 20),
        ("Small Meeting Room", 10)
    ]
    cursor.executemany("INSERT INTO Rooms (room_name, capacity) VALUES (?, ?);", rooms)
    
    # Insert sample personnel (librarians, staff, volunteers, etc.)
    personnel = [
        ("Alice", "Smith", "F", "1998-04-30", "alice.smith@library.org", "123-456-7890", "302 Happy Street", "Member"),
        ("Bob", "Johnson", "M", "1976-08-15", "bob.johnson@library.org", "234-567-8901", None, "Staff"),
        ("Carol", "Williams", "Other", "2000-01-01", "carol.williams@library.org", None, None, "Volunteer"),
        ("David", "Brown", "M", "1985-06-22", "david.brown@library.org", "345-678-9012", "789 Maple Ave", "Member"),
        ("Emma", "Davis", "F", "1992-11-10", "emma.davis@library.org", None, "456 Oak Lane", "Staff"),
        ("Frank", "Miller", "M", "1970-03-05", "frank.miller@library.org", "567-890-1234", None, "Volunteer"),
        ("Grace", "Wilson", "F", "2003-07-19", "grace.wilson@library.org", "678-901-2345", "101 Birch Blvd", "Member"),
        ("Henry", "Anderson", "M", "1999-12-25", "henry.anderson@library.org", None, None, "Member"),
        ("Isabel", "Martinez", "F", "1988-09-14", None, "789-012-3456", "55 Cedar Drive", "Staff"),
        ("Jack", "Taylor", "Other", "1995-02-28", "jack.taylor@library.org", None, "900 Elm St", "Volunteer")
    ]
    cursor.executemany("""
        INSERT INTO Personnel (first_name, last_name, gender, birth_date, email, phone, address, role) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, personnel)
    
    # Insert sample items (at least 10 entries)
    items = [
        ("The Great Gatsby", "print_book", "F. Scott Fitzgerald", "Scribner", 1925, "9780743273565", 3),
        ("1984", "print_book", "George Orwell", "Secker & Warburg", 1949, "9780451524935", 5),
        ("Digital Fortress", "online_book", "Dan Brown", "St. Martin's Press", 1998, "9780312263126", 10),
        ("National Geographic", "magazine", None, "National Geographic Society", 2020, None, 7),
        ("Science Journal", "journal", None, "American Science Association", 2021, None, 6),
        ("Greatest Hits", "cd", "Various", "Sony Music", 2005, None, 4),
        ("Classic Rock", "record", "Various", "Warner Records", 1995, None, 2),
        ("Python Programming", "print_book", "John Zelle", "Franklin, Beedle & Associates", 2010, "9781590282755", 8),
        ("Modern Art", "magazine", None, "Art & Design Publishing", 2018, None, 5),
        ("The Future of AI", "journal", None, "Tech Journal Press", 2022, None, 3)
    ]
    cursor.executemany("""
    INSERT INTO Items (title, item_type, author, publisher, publication_year, ISBN, available_copies)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, items)
    
    # Insert sample events (10 entries)
    events = [
        ("Storytime for Kids", "2025-04-10", "10:00 AM", "children", 1),
        ("Evening Book Club", "2025-04-15", "06:30 PM", "adults", 2),
        ("Tech Workshop: Python Basics", "2025-05-02", "03:00 PM", "both", 3),
        ("Author Meet & Greet: Sci-Fi Special", "2025-05-12", "02:00 PM", "adults", 1),
        ("Family Movie Night", "2025-06-01", "07:00 PM", "both", 2),
        ("Lego Builders Club", "2025-06-10", "11:00 AM", "children", 1),
        ("Financial Planning Seminar", "2025-06-18", "05:00 PM", "adults", 2),
        ("Poetry Reading Night", "2025-07-08", "06:00 PM", "both", 3),
        ("Crafts & Creativity Workshop", "2025-07-22", "01:30 PM", "children", 1),
        ("History Lecture: Ancient Civilizations", "2025-08-05", "04:00 PM", "adults", 2)
    ]
    cursor.executemany("""
    INSERT INTO Events (event_name, event_date, event_time, recommended_audience, room_id)
    VALUES (?, ?, ?, ?, ?);
    """, events)
    
    # Insert sample event registrations (10 entries)
    event_regs = [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 6),
        (7, 7),
        (8, 8),
        (9, 9),
        (10, 10)
    ]
    for user_id, event_id in event_regs:
        cursor.execute("INSERT INTO EventRegistrations (user_id, event_id) VALUES (?, ?);", (user_id, event_id))
    
    # Insert sample volunteer registrations (5 entries)
    volunteers = [
        (1, 2),
        (2, 4),
        (3, 1),
        (4, 1),
        (5, 3)
    ]
    cursor.executemany("""
    INSERT INTO VolunteerRegistrations (user_id, event_id) VALUES (?, ?);
    """, volunteers)
    
    # Insert sample help requests (10 entries)
    help_requests = [
        (1, 1, "Need help finding a book on history", "pending"),
        (2, 2, "Assistance with borrowing procedure", "pending"),
        (3, 1, "Question about fines", "pending"),
        (4, None, "Looking for upcoming events", "pending"),
        (5, 2, "Help with the catalog", "pending"),
        (6, None, "Need computer assistance", "pending"),
        (7, 3, "Inquiry about volunteering", "pending"),
        (8, 1, "Question on new arrivals", "pending"),
        (9, 2, "Help with digital resources", "pending"),
        (10, 3, "Assistance with research", "pending")
    ]
    cursor.executemany("""
    INSERT INTO HelpRequests (user_id, librarian_id, description, status)
    VALUES (?, ?, ?, ?);
    """, help_requests)
    
    conn.commit()

# -----------------------------
# Application Functions
# -----------------------------

def find_item(conn, column, value):
    try:
        cursor = conn.cursor()
        query = f"SELECT * FROM Items WHERE {column} LIKE ?"
        cursor.execute(query, (f"%{value}%",))
        results = cursor.fetchall()

        if results:
            for row in results:
                print(row)
        else:
            print(f"No items found with {column} containing '{value}'.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}. Please make sure the column '{column}' exists.")

def borrow_item(conn, user_id, item_id):
    cursor = conn.cursor()
    # Check available copies
    cursor.execute("SELECT available_copies FROM Items WHERE item_id = ?", (item_id,))
    result = cursor.fetchone()
    if result is None:
        print("Item not found.")
        return
    available = result[0]
    if available <= 0:
        print("No available copies for this item.")
        return

    borrow_date = datetime.date.today().isoformat()
    due_date = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
    try:
        cursor.execute("""
        INSERT INTO BorrowTransactions (user_id, item_id, borrow_date, due_date)
        VALUES (?, ?, ?, ?);
        """, (user_id, item_id, borrow_date, due_date))
        # Decrement available copies
        cursor.execute("UPDATE Items SET available_copies = available_copies - 1 WHERE item_id = ?;", (item_id,))
        # If no copies left, update status to 'borrowed'
        cursor.execute("SELECT available_copies FROM Items WHERE item_id = ?;", (item_id,))
        new_available = cursor.fetchone()[0]
        if new_available <= 0:
            cursor.execute("UPDATE Items SET status = 'borrowed' WHERE item_id = ?;", (item_id,))
        conn.commit()
        print("Item borrowed successfully.")
    except sqlite3.Error as e:
        print("Error borrowing item:", e)

def get_active_borrow_transactions(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT transaction_id, item_id, borrow_date, due_date 
    FROM BorrowTransactions 
    WHERE user_id = ? AND return_date IS NULL;
    """, (user_id,))
    return cursor.fetchall()

def return_item(conn, transaction_id, return_date=None):
    cursor = conn.cursor()
    if return_date is None:
        return_date = datetime.date.today().isoformat()
    try:
        # Get the item_id for the transaction
        cursor.execute("SELECT item_id FROM BorrowTransactions WHERE transaction_id = ? AND return_date IS NULL", (transaction_id,))
        row = cursor.fetchone()
        if row is None:
            print("No active borrow transaction found with that ID.")
            return
        item_id = row[0]
        cursor.execute("""
        UPDATE BorrowTransactions 
        SET return_date = ? 
        WHERE transaction_id = ?;
        """, (return_date, transaction_id))
        # Increment available copies
        cursor.execute("UPDATE Items SET available_copies = available_copies + 1 WHERE item_id = ?;", (item_id,))
        cursor.execute("UPDATE Items SET status = 'available' WHERE item_id = ?;", (item_id,))
        conn.commit()
        print("Item returned successfully.")
    except sqlite3.Error as e:
        print("Error returning item:", e)

def donate_item(conn, user_id, title, author, publication_year, item_type, condition, location="Donation Desk"):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO Items (title, author, publication_year, item_type, status, location, available_copies)
        VALUES (?, ?, ?, ?, 'donated', ?, 1);
        """, (title, author, publication_year, item_type, location))
        item_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO Donations (user_id, item_id, condition)
        VALUES (?, ?, ?);
        """, (user_id, item_id, condition))
        conn.commit()
        print("Item donated successfully.")
    except sqlite3.Error as e:
        print("Error donating item:", e)

def find_event(conn, event_name):
    cursor = conn.cursor()
    if event_name.strip() == "":
        cursor.execute("SELECT * FROM Events;")
    else:
        cursor.execute("SELECT * FROM Events WHERE event_name LIKE ?", (f"%{event_name}%",))
    return cursor.fetchall()

def register_event(conn, user_id, event_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO EventRegistrations (user_id, event_id)
        VALUES (?, ?);
        """, (user_id, event_id))
        conn.commit()
        print("Registered for event successfully.")
    except sqlite3.Error as e:
        print("Error registering for event:", e)

def volunteer_for_library(conn, user_id, event_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO VolunteerRegistrations (user_id, event_id)
        VALUES (?, ?);
        """, (user_id, event_id))
        conn.commit()
        print("Volunteer registration successful.")
    except sqlite3.Error as e:
        print("Error in volunteer registration:", e)

def ask_for_help(conn, user_id, description, librarian_id=None):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO HelpRequests (user_id, librarian_id, description)
        VALUES (?, ?, ?);
        """, (user_id, librarian_id, description))
        conn.commit()
        print("Help request submitted.")
    except sqlite3.Error as e:
        print("Error submitting help request:", e)

# -----------------------------
# Utility Functions for Debug
# -----------------------------

def drop_all_tables(conn):
    conn.execute("PRAGMA foreign_keys = OFF;")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        if table_name != 'sqlite_sequence':
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.execute("PRAGMA foreign_keys = ON;")

def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table[0]}")

def print_table(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    print("\t".join(columns))
    print("-" * 50)
    for row in rows:
        print("\t".join(map(str, row)))

# -----------------------------
# Main Execution Block
# -----------------------------

if __name__ == '__main__':
    conn = create_connection()
    drop_all_tables(conn)
    create_tables(conn)
    populate_sample_data(conn)

    user_input = ""
    while user_input != "9":
        print("""Available Actions:
1. Find an item in the library
2. Borrow an item
3. Return a borrowed item
4. Donate an item
5. Find an event
6. Register for an event
7. Volunteer for an event
8. Ask for help
9. End""")
        user_input = input("Please choose action: ").strip()

        if user_input == "1":
            column = input("Search by (Title, Type, Author, Publisher, Year, ISBN): ").strip()
            # Map input to column names
            if column.lower() == "type":
                column = "item_type"
            elif column.lower() == "year":
                column = "publication_year"
            else:
                column = column.lower()
            value = input("Enter search value: ").strip()
            find_item(conn, column, value)
        
        elif user_input == "2":
            user_id = input("Enter your user ID: ").strip()
            item_id = input("Enter the ID of the item to borrow: ").strip()
            borrow_item(conn, user_id, item_id)
        
        elif user_input == "3":
            user_id = input("Enter your user ID: ").strip()
            transactions = get_active_borrow_transactions(conn, user_id)
            if not transactions:
                print("No active borrow transactions found.")
            else:
                print("Active Borrow Transactions:")
                for trans in transactions:
                    print(f"Transaction ID: {trans[0]}, Item ID: {trans[1]}, Borrow Date: {trans[2]}, Due Date: {trans[3]}")
                trans_id = input("Enter the Transaction ID you want to return: ").strip()
                return_item(conn, trans_id)
        
        elif user_input == "4":
            user_id = input("Enter your user ID: ").strip()
            title = input("Enter the title of the donated item: ").strip()
            author = input("Enter the author (if applicable, else leave blank): ").strip()
            publication_year = input("Enter the publication year: ").strip()
            item_type = input("Enter the item type (print_book, online_book, magazine, journal, cd, record): ").strip()
            condition = input("Enter the condition of the item: ").strip()
            location = input("Enter donation location (or press Enter for default 'Donation Desk'): ").strip()
            if location == "":
                location = "Donation Desk"
            donate_item(conn, user_id, title, author, publication_year, item_type, condition, location)
        
        elif user_input == "5":
            event_name = input("Enter event name to search (or press Enter to list all events): ").strip()
            events = find_event(conn, event_name)
            if events:
                for event in events:
                    print(event)
            else:
                print("No events found.")
        
        elif user_input == "6":
            user_id = input("Enter your user ID: ").strip()
            event_id = input("Enter the event ID to register for: ").strip()
            register_event(conn, user_id, event_id)
        
        elif user_input == "7":
            user_id = input("Enter your user ID: ").strip()
            event_id = input("Enter the event ID to volunteer for: ").strip()
            volunteer_for_library(conn, user_id, event_id)
        
        elif user_input == "8":
            user_id = input("Enter your user ID: ").strip()
            description = input("Enter your help request description: ").strip()
            librarian_id = input("Enter librarian ID (if known, else leave blank): ").strip()
            if librarian_id == "":
                librarian_id = None
            ask_for_help(conn, user_id, description, librarian_id)
        
        elif user_input.lower() == "check":
            get_tables(conn)
            table_name = input("Enter table name to display: ").strip()
            print_table(conn, table_name)
        
        elif user_input != "9":
            print("Invalid input. Please try again.")
        
        print("\n")
    
    print("Thank you for using our service. See you next time!")
    conn.close()
