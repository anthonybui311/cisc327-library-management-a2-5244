"""
Comprehensive unit tests for library_service.py functions
Tests all business logic functions implementing requirements R1-R7
"""

import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books
)
from library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    return_book_by_patron,
    calculate_late_fee_for_book,
    search_books_in_catalog,
    get_patron_status_report
)


# This run before each test function to make sure we have a clean database
from database import init_database, add_sample_data

@pytest.fixture(autouse=True)
def setup_test_database():
    """Set up a clean database for each test"""
    # Remove existing test database if it exists
    if os.path.exists('library.db'):
        os.remove('library.db')
    
    # Initialize fresh database with sample data
    init_database()
    add_sample_data()
    
    yield
    
    # Clean up after test
    if os.path.exists('library.db'):
        os.remove('library.db')


class TestAddBookToCatalog:
    """Test R1: Add Book To Catalog functionality"""
    
    # Test 1: Valid input
    def test_add_book_valid_input1(self):
        """Test adding a book with valid input"""
        success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
        assert success == True
        assert "successfully added" in message.lower()
    
    # Test 2: Another valid input
    def test_add_book_valid_input2(self):
        """Test adding a book with valid input"""
        success, message = add_book_to_catalog("A random book for testing", "A random name for testing", "1234566890123", 1)
        assert success == True
        assert "successfully added" in message.lower()
    
    # Test 3: Invalid inputs
    def test_add_book_empty_title(self):
        """Test adding a book with empty title"""
        success, message = add_book_to_catalog("", "Test Author", "1234567890123", 5)
        assert success == False
        assert "Title is required" in message
    
    # Test 4: Invalid inputs
    def test_add_book_whitespace_title(self):
        """Test adding a book with whitespace-only title"""
        success, message = add_book_to_catalog("   ", "Test Author", "1234567890123", 5)
        assert success == False
        assert "Title is required" in message
    
    # Test 5: Invalid inputs
    def test_add_book_empty_author(self):
        """Test adding a book with empty author"""
        success, message = add_book_to_catalog("Test Book", "", "1234567890123", 5)
        assert success == False
        assert "Author is required" in message
        
    # Test 6: Invalid inputs
    def test_add_book_whitespace_author(self):
        """Test adding a book with whitespace-only author"""
        success, message = add_book_to_catalog("Test Book", "   ", "1234567890123", 5)
        assert success == False
        assert "Author is required" in message

    # Test 7: Invalid inputs
    def test_add_book_title_too_long(self):
        """Test adding a book with title exceeding 200 characters"""
        long_title = "A" * 201  # 201 characters
        success, message = add_book_to_catalog(long_title, "Test Author", "1234567890123", 5)
        assert success == False
        assert "Title must be less than 200 characters." in message
    
    # Test 8: Invalid inputs
    def test_add_book_author_too_long(self):
        """Test adding a book with author exceeding 100 characters"""
        long_author = "A" * 101  # 101 characters
        success, message = add_book_to_catalog("Test Book", long_author, "1234567890123", 5)
        assert success == False
        assert "Author must be less than 100 characters." in message
    
    # Test 9: Invalid inputs
    def test_add_book_invalid_isbn_too_short(self):
        """Test adding a book with ISBN too short"""
        success, message = add_book_to_catalog("Test Book", "Test Author", "123456789", 5)
        assert success == False
        assert "13 digits" in message
    
    # Test 10: Invalid inputs
    def test_add_book_invalid_isbn_too_long(self):
        """Test adding a book with ISBN too long"""
        success, message = add_book_to_catalog("Test Book", "Test Author", "12345678901234", 5)
        assert success == False
        assert "13 digits" in message
    
    # Test 11: Invalid inputs
    def test_add_book_invalid_isbn_non_numeric(self):
        """Test adding a book with non-numeric ISBN"""
        success, message = add_book_to_catalog("Test Book", "Test Author", "123456789012A", 5)
        assert success == False
        assert "13 digits" in message
    
    # Test 12: Invalid inputs
    def test_add_book_zero_copies(self):
        """Test adding a book with zero copies"""
        success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 0)
        assert success == False
        assert "Total copies must be a positive integer." in message

    # Test 13: Check duplicate ISBN
    def test_add_book_duplicate_isbn(self):
        """Test adding a book with an ISBN that already exists"""

        # Try adding another book with same ISBN
        success, message = add_book_to_catalog("Another Book", "Another Author", "9780451524935", 2)
        assert success == False
        assert "A book with this ISBN already exists." in message


    """Test R2: Book Catalog Display functionality
    was tested manually via web interface. It contains all of the required features:
    - Displays all books with title, author, ISBN, available copies/total copies
    - Action (Borrow button for available books)"""
    



class TestBorrowBookByPatron:
    """Test R3: Book Borrowing Interface functionality"""
    
    # Test 1: Valid input
    def test_borrow_book_valid_input(self):
        """Test borrowing a book with valid patron and book"""
        # Calculate expected due date (current date + 14 days)
        expected_due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        success, message = borrow_book_by_patron("123456", 1)
    
        assert success == True
        # By default, the sample data has "The Great Gatsby" with book_id=1
        assert f'Successfully borrowed "The Great Gatsby". Due date: {expected_due_date}.' in message
    
    # Test 2: Invalid patron ID (too short)
    def test_borrow_book_invalid_patron_id_too_short(self):
        """Test borrowing with patron ID too short"""
        success, message = borrow_book_by_patron("12345", 1)
        assert success == False
        assert "Invalid patron ID. Must be exactly 6 digits." in message

    # Test 3: Invalid patron ID (too long)
    def test_borrow_book_invalid_patron_id_too_long(self):
        """Test borrowing with patron ID too long"""
        success, message = borrow_book_by_patron("1234567", 1)
        assert success == False
        assert "Invalid patron ID. Must be exactly 6 digits." in message
    
    # Test 4: Invalid patron ID (non-numeric)
    def test_borrow_book_invalid_patron_id_non_numeric(self):
        """Test borrowing with non-numeric patron ID"""
        success, message = borrow_book_by_patron("12345A", 1)
        assert success == False
        assert "Invalid patron ID. Must be exactly 6 digits." in message
    
    # Test 5: Non-existent book
    def test_borrow_book_nonexistent_book(self):
        """Test borrowing a book that doesn't exist"""
        success, message = borrow_book_by_patron("123456", 99999)
        assert success == False
        assert "Book not found." in message
    
    # Test 6: Unavailable book
    def test_borrow_book_unavailable_book(self):
        """Test borrowing when no copies available"""
        # By default, "1984" with book_id=3, has availability set to not available
        success, message = borrow_book_by_patron("123456", 3)
        assert success == False
        assert "This book is currently not available." in message
        
    # Test 7: Patron limit exceeded
    def test_borrow_book_patron_limit_exceeded(self):
        """Test borrowing when patron already has 5 books (max limit)"""
        # I add a random book name with availability 5 to the database,
        # book id will be 4 since there are 3 default books (1, 2, 3)
        add_book_to_catalog("Test Book 1", "Test Author", "1234567890123", 5)
        # Then I use patron id 123456 to borrow 5 books
        for book_id in range(5):
            borrow_book_by_patron("123456", 4)
        
        success, message = borrow_book_by_patron("123456", 2)
        assert success == False
        assert "You have reached the maximum borrowing limit of 5 books." in message
    
    # Test 8: Check borowing record creation and availability update
    def test_borrow_book_record_and_availability(self):
        """Test that borrowing a book creates a borrow record and updates availability"""
        # Before borrowing, check available copies of book_id=1
        book_before = get_book_by_id(1)
        if not book_before:
            pytest.fail("Book with ID 1 should exist in sample data")
        available_before = book_before['available_copies']
        
        # Use new patron id to avoid limit issues
        success, message = borrow_book_by_patron("124653", 1)
        assert success == True
        
        # After borrowing, check available copies again
        book_after = get_book_by_id(1)
        if not book_after:
            pytest.fail("Book with ID 1 should exist in sample data")
        available_after = book_after['available_copies']
        
        assert available_after == available_before - 1
        
        # Check that borrow record exists
        borrow_count = get_patron_borrow_count("124653")
        assert borrow_count == 1


class TestReturnBookByPatron:
    """Test R4: Book Return Processing functionality"""

    def test_return_book_not_implemented(self):
        """Test returning a book that wasn't borrowed by this patron"""
        success, message = return_book_by_patron("123456", 1)
        assert success == False
        assert "Book return functionality is not yet implemented." in message


class TestCalculateLateFeeForBook:
    """Test R5: Late Fee Calculation API functionality"""
    
    def test_calculate_late_fee_not_implemented(self):
        """Test late fee calculation when not implemented"""
        result = calculate_late_fee_for_book("123456", 1)
        assert isinstance(result, dict)
        assert result == {}


class TestSearchBooksInCatalog:
    """Test R6: Book Search Functionality"""
    
    def test_search_by_title_not_implemented(self):
        """Test search by title with partial matching"""
        results = search_books_in_catalog("Python", "title")
        assert isinstance(results, list)
        assert results == []
        
class TestGetPatronStatusReport:
    """Test R7: Patron Status Report functionality"""
    
    def test_patron_status_not_implemented(self):
        report = get_patron_status_report("123456")
        # Should return dict with patron information
        assert isinstance(report, dict)
        assert report == {}
