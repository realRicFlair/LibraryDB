import sqlite3
import datetime

def create_connection(db_file="library.db"):
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    
    # Table for library items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        publication_year INTEGER,
        item_type TEXT CHECK(item_type IN ('print_book', 'online_book', 'magazine', 'journal', 'cd', 'record')),
        status TEXT CHECK(status IN ('available', 'borrowed', 'reserved', 'donated', 'future')) DEFAULT 'available',
        location TEXT
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
        FOREIGN KEY(user_id) REFERENCES Users(user_id),
        FOREIGN KEY(item_id) REFERENCES Items(item_id)
    );
    """)
    
    # Table for library users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT
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
        FOREIGN KEY(user_id) REFERENCES Users(user_id),
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
    
    # Table for social rooms
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SocialRooms (
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
        event_description TEXT,
        recommended_audience TEXT,
        room_id INTEGER NOT NULL,
        FOREIGN KEY(room_id) REFERENCES SocialRooms(room_id)
    );
    """)
    
    # Table for event registrations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EventRegistrations (
        registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        registration_date DATE DEFAULT (DATE('now')),
        FOREIGN KEY(user_id) REFERENCES Users(user_id),
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
             (SELECT capacity FROM SocialRooms WHERE room_id = (SELECT room_id FROM Events WHERE event_id = NEW.event_id)))
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
        role TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT
    );
    """)
    
    # Table for volunteer registrations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS VolunteerRegistrations (
        volunteer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        start_date DATE DEFAULT (DATE('now')),
        role TEXT,
        FOREIGN KEY(user_id) REFERENCES Users(user_id)
    );
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
        FOREIGN KEY(user_id) REFERENCES Users(user_id),
        FOREIGN KEY(librarian_id) REFERENCES Personnel(personnel_id)
    );
    """)
    
    conn.commit()

def populate_sample_data(conn):
    cursor = conn.cursor()
    
    # Insert sample social rooms (at least 3 entries)
    social_rooms = [
        ("Main Hall", 50),
        ("Conference Room", 20),
        ("Small Meeting Room", 10)
    ]
    cursor.executemany("INSERT INTO SocialRooms (room_name, capacity) VALUES (?, ?);", social_rooms)
    
    # Insert sample personnel (librarians, etc.)
    personnel = [
        ("Alice", "Smith", "librarian", "alice.smith@library.org", "123-456-7890"),
        ("Bob", "Johnson", "administrator", "bob.johnson@library.org", "234-567-8901"),
        ("Carol", "Williams", "librarian", "carol.williams@library.org", "345-678-9012")
    ]
    cursor.executemany("INSERT INTO Personnel (first_name, last_name, role, email, phone) VALUES (?, ?, ?, ?, ?);", personnel)
    
    # Insert sample users (at least 10 entries)
    users = [
        ("John", "Doe", "john.doe@example.com", "111-111-1111", "123 Maple St"),
        ("Jane", "Doe", "jane.doe@example.com", "222-222-2222", "456 Oak Ave"),
        ("Mike", "Brown", "mike.brown@example.com", "333-333-3333", "789 Pine Rd"),
        ("Emily", "Davis", "emily.davis@example.com", "444-444-4444", "321 Birch Ln"),
        ("David", "Wilson", "david.wilson@example.com", "555-555-5555", "654 Cedar Ct"),
        ("Sophia", "Taylor", "sophia.taylor@example.com", "666-666-6666", "987 Spruce Dr"),
        ("Daniel", "Anderson", "daniel.anderson@example.com", "777-777-7777", "159 Elm St"),
        ("Olivia", "Thomas", "olivia.thomas@example.com", "888-888-8888", "753 Walnut Ave"),
        ("Liam", "Jackson", "liam.jackson@example.com", "999-999-9999", "852 Fir Blvd"),
        ("Ava", "White", "ava.white@example.com", "000-000-0000", "951 Poplar Rd")
    ]
    cursor.executemany("INSERT INTO Users (first_name, last_name, email, phone, address) VALUES (?, ?, ?, ?, ?);", users)
    
    # Insert sample items (at least 10 entries)
    items = [
        ("The Great Gatsby", "F. Scott Fitzgerald", 1925, "print_book", "available", "Shelf A1"),
        ("1984", "George Orwell", 1949, "print_book", "available", "Shelf A2"),
        ("Digital Fortress", "Dan Brown", 1998, "online_book", "available", "Online"),
        ("National Geographic", None, 2020, "magazine", "available", "Shelf B1"),
        ("Science Journal", None, 2021, "journal", "available", "Shelf C1"),
        ("Greatest Hits", "Various", 2005, "cd", "available", "Shelf D1"),
        ("Classic Rock", "Various", 1995, "record", "available", "Shelf D2"),
        ("Python Programming", "John Zelle", 2010, "print_book", "available", "Shelf A3"),
        ("Modern Art", None, 2018, "magazine", "available", "Shelf B2"),
        ("The Future of AI", None, 2022, "journal", "future", "Pending")
    ]
    cursor.executemany("""
    INSERT INTO Items (title, author, publication_year, item_type, status, location)
    VALUES (?, ?, ?, ?, ?, ?);
    """, items)
    
    # Insert sample borrow transactions (10 entries)
    today = datetime.date.today().isoformat()
    due = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
    borrow_transactions = [
        (1, 1, today, due, None, 0),  # John borrows "The Great Gatsby"
        (2, 2, today, due, None, 0),
        (3, 3, today, due, None, 0),
        (4, 4, today, due, None, 0),
        (5, 5, today, due, None, 0),
        (6, 6, today, due, None, 0),
        (7, 7, today, due, None, 0),
        (8, 8, today, due, None, 0),
        (9, 9, today, due, None, 0),
        (10, 10, today, due, None, 0)
    ]
    cursor.executemany("""
    INSERT INTO BorrowTransactions (user_id, item_id, borrow_date, due_date, return_date, fine)
    VALUES (?, ?, ?, ?, ?, ?);
    """, borrow_transactions)
    
    # Insert sample events (10 entries)
    events = [
        ("Book Club Meeting", "2025-04-10", "Monthly book discussion", "adults", 1),
        ("Children Story Time", "2025-04-12", "Stories for children", "children", 3),
        ("Art Show", "2025-04-15", "Local art exhibit", "general", 2),
        ("Film Screening", "2025-04-18", "Classic movie screening", "general", 1),
        ("Sci-Fi Meetup", "2025-04-20", "Discussion on science fiction books", "adults", 2),
        ("Photography Workshop", "2025-04-22", "Learn the basics of photography", "adults", 3),
        ("Local History Talk", "2025-04-25", "Talk about local heritage", "general", 1),
        ("Poetry Reading", "2025-04-27", "Open mic for poetry", "adults", 2),
        ("Tech Meetup", "2025-04-29", "Discussion on emerging tech", "adults", 1),
        ("Cooking Demo", "2025-05-01", "Demonstration of healthy recipes", "general", 3)
    ]
    cursor.executemany("""
    INSERT INTO Events (event_name, event_date, event_description, recommended_audience, room_id)
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
        (1, "Event Helper"),
        (2, "Shelf Organizer"),
        (3, "Event Helper"),
        (4, "Receptionist"),
        (5, "Community Outreach")
    ]
    cursor.executemany("""
    INSERT INTO VolunteerRegistrations (user_id, role) VALUES (?, ?);
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
    # Note: Some help requests may not have a librarian assigned yet (NULL librarian_id)
    cursor.executemany("""
    INSERT INTO HelpRequests (user_id, librarian_id, description, status)
    VALUES (?, ?, ?, ?);
    """, help_requests)
    
    conn.commit()

# Sample functions for the database application

def find_item(conn, title):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Items WHERE title LIKE ?", (f"%{title}%",))
    return cursor.fetchall()

def borrow_item(conn, user_id, item_id):
    cursor = conn.cursor()
    borrow_date = datetime.date.today().isoformat()
    due_date = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
    try:
        cursor.execute("""
        INSERT INTO BorrowTransactions (user_id, item_id, borrow_date, due_date)
        VALUES (?, ?, ?, ?);
        """, (user_id, item_id, borrow_date, due_date))
        # Update item status to 'borrowed'
        cursor.execute("UPDATE Items SET status = 'borrowed' WHERE item_id = ?;", (item_id,))
        conn.commit()
        print("Item borrowed successfully.")
    except sqlite3.Error as e:
        print("Error borrowing item:", e)

def return_item(conn, transaction_id, return_date=None):
    cursor = conn.cursor()
    if return_date is None:
        return_date = datetime.date.today().isoformat()
    try:
        cursor.execute("""
        UPDATE BorrowTransactions 
        SET return_date = ? 
        WHERE transaction_id = ?;
        """, (return_date, transaction_id))
        # Optionally, update item status back to 'available'
        cursor.execute("""
        UPDATE Items 
        SET status = 'available' 
        WHERE item_id = (SELECT item_id FROM BorrowTransactions WHERE transaction_id = ?);
        """, (transaction_id,))
        conn.commit()
        print("Item returned successfully.")
    except sqlite3.Error as e:
        print("Error returning item:", e)

def donate_item(conn, user_id, title, author, publication_year, item_type, condition, location="Donation Desk"):
    cursor = conn.cursor()
    try:
        # Insert donated item into Items with status 'donated'
        cursor.execute("""
        INSERT INTO Items (title, author, publication_year, item_type, status, location)
        VALUES (?, ?, ?, ?, 'donated', ?);
        """, (title, author, publication_year, item_type, location))
        item_id = cursor.lastrowid
        # Record the donation
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

def volunteer_for_library(conn, user_id, role):
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO VolunteerRegistrations (user_id, role)
        VALUES (?, ?);
        """, (user_id, role))
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

# Main execution block
if __name__ == '__main__':
    conn = create_connection()
    create_tables(conn)
    populate_sample_data(conn)
    
    # Example usage:
    print("Finding item '1984':")
    items_found = find_item(conn, "1984")
    for item in items_found:
        print(item)
    
    print("\nBorrowing item_id 1 by user_id 1:")
    borrow_item(conn, 1, 1)
    
    print("\nReturning transaction_id 1:")
    return_item(conn, 1)
    
    print("\nDonating a new item by user_id 2:")
    donate_item(conn, 2, "New Horizons", "Jane Doe", 2023, "print_book", "Good condition")
    
    print("\nFinding event 'Art Show':")
    events_found = find_event(conn, "Art Show")
    for event in events_found:
        print(event)
    
    print("\nRegistering user_id 3 for event_id 1:")
    register_event(conn, 3, 1)
    
    print("\nUser_id 4 volunteers as 'Event Helper':")
    volunteer_for_library(conn, 4, "Event Helper")
    
    print("\nUser_id 5 asks for help:")
    ask_for_help(conn, 5, "I need assistance locating the digital archives.")
    
    conn.close()
