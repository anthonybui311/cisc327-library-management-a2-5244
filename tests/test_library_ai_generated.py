"""
Task 3: AI-Generated Comprehensive Test Suite
Generated using: GitHub Copilot Chat (GPT-4)
Date: October 13, 2025

Comprehensive unit tests for library service functions with extensive coverage
including happy paths, edge cases, error handling, parameterized tests, and integration scenarios.
"""

import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch, MagicMock

from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_db_connection,
    init_database, add_sample_data, get_patron_borrowed_books
)
from library_service import (
    add_book_to_catalog,
    borrow_book_by_patron,
    return_book_by_patron,
    calculate_late_fee_for_book,
    search_books_in_catalog,
    get_patron_status_report
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_database():
    """Set up a clean database for each test"""
    if os.path.exists('library.db'):
        os.remove('library.db')
    
    init_database()
    add_sample_data()
    
    yield
    
    if os.path.exists('library.db'):
        os.remove('library.db')


@pytest.fixture
def sample_patron_id():
    """Provide a valid patron ID for testing"""
    return "123456"


@pytest.fixture
def sample_book_id():
    """Provide a valid book ID for testing"""
    return 1


@pytest.fixture
def borrowed_book_setup(sample_patron_id, sample_book_id):
    """Setup: Patron has borrowed a book"""
    borrow_book_by_patron(sample_patron_id, sample_book_id)
    return sample_patron_id, sample_book_id


@pytest.fixture
def overdue_book_setup(sample_patron_id, sample_book_id):
    """Setup: Patron has an overdue book"""
    borrow_book_by_patron(sample_patron_id, sample_book_id)
    
    conn = get_db_connection()
    past_due = (datetime.now() - timedelta(days=10)).isoformat()
    conn.execute('''
        UPDATE borrow_records 
        SET due_date = ? 
        WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
    ''', (past_due, sample_patron_id, sample_book_id))
    conn.commit()
    conn.close()
    
    return sample_patron_id, sample_book_id


# ============================================================================
# Parameterized Test Data
# ============================================================================

INVALID_PATRON_IDS = [
    ("12345", "too_short"),
    ("1234567", "too_long"),
    ("12345A", "contains_letter"),
    ("ABCDEF", "all_letters"),
    ("", "empty_string"),
    ("   ", "whitespace"),
    ("123-456", "contains_hyphen"),
    ("123 456", "contains_space"),
    ("123$56", "contains_special_char"),
]

OVERDUE_FEE_CALCULATIONS = [
    (1, 0.50),
    (5, 2.50),
    (7, 3.50),
    (10, 5.00),
    (14, 7.00),
    (30, 15.00),
    (60, 30.00),
    (100, 50.00),
]

SEARCH_SCENARIOS = [
    ("gatsby", "title", 1, True),  # (search_term, search_type, expected_count, should_find)
    ("ORWELL", "author", 1, True),
    ("", "title", 0, False),
    ("NonExistent", "title", 0, False),
    ("9780743273565", "isbn", 1, True),
    ("partial_isbn", "isbn", 0, False),
]


# ============================================================================
# Test Class: return_book_by_patron() - AI Generated
# ============================================================================

class TestReturnBookByPatronAI:
    """AI-Generated comprehensive tests for book return functionality"""
    
    def test_return_book_happy_path(self, borrowed_book_setup):
        """Happy path: Successfully return a borrowed book"""
        patron_id, book_id = borrowed_book_setup
        
        success, message = return_book_by_patron(patron_id, book_id)
        
        assert success is True
        assert "Successfully returned" in message
        assert "The Great Gatsby" in message
    
    @pytest.mark.parametrize("invalid_id,reason", INVALID_PATRON_IDS)
    def test_return_book_invalid_patron_ids(self, invalid_id, reason):
        """Test return with various invalid patron ID formats"""
        success, message = return_book_by_patron(invalid_id, 1)
        
        assert success is False
        assert "Invalid patron ID" in message
    
    def test_return_book_nonexistent_book(self, sample_patron_id):
        """Test returning a book that doesn't exist in database"""
        success, message = return_book_by_patron(sample_patron_id, 99999)
        
        assert success is False
        assert "Book not found" in message
    
    def test_return_book_not_borrowed_by_patron(self, sample_patron_id):
        """Test patron trying to return book they didn't borrow"""
        success, message = return_book_by_patron(sample_patron_id, 1)
        
        assert success is False
        assert "No active borrow record" in message
    
    def test_return_book_already_returned(self, borrowed_book_setup):
        """Test double return attempt - should fail on second attempt"""
        patron_id, book_id = borrowed_book_setup
        
        # First return succeeds
        success1, _ = return_book_by_patron(patron_id, book_id)
        assert success1 is True
        
        # Second return fails
        success2, message2 = return_book_by_patron(patron_id, book_id)
        assert success2 is False
        assert "No active borrow record" in message2
    
    def test_return_book_increments_availability(self, borrowed_book_setup):
        """Verify available_copies increments correctly"""
        patron_id, book_id = borrowed_book_setup
        
        book_before = get_book_by_id(book_id)
        assert book_before is not None, "Book should exist before return"
        available_before = book_before['available_copies']
        
        return_book_by_patron(patron_id, book_id)
        
        book_after = get_book_by_id(book_id)
        assert book_after is not None, "Book should exist after return"
        assert book_after['available_copies'] == available_before + 1
    
    def test_return_book_with_zero_availability_before(self):
        """Test returning book when available_copies was 0"""
        # Borrow the only available copy of book 3 (1984)
        add_book_to_catalog("Single Copy Book", "Author", "9999999999999", 1)
        book = get_book_by_isbn("9999999999999")
        assert book is not None, "Book should be found after adding to catalog"
        book_id = book['id']
        
        patron_id = "111111"
        borrow_book_by_patron(patron_id, book_id)
        
        # Verify 0 available
        book_check = get_book_by_id(book_id)
        assert book_check is not None, "Book should exist in database"
        assert book_check['available_copies'] == 0
        
        # Return should make it 1
        return_book_by_patron(patron_id, book_id)
        
        book_after = get_book_by_id(book_id)
        assert book_after is not None, "Book should exist after return"
        assert book_after['available_copies'] == 1
    
    def test_return_book_updates_borrow_record(self, borrowed_book_setup):
        """Verify return_date is set in borrow_records table"""
        patron_id, book_id = borrowed_book_setup
        
        return_book_by_patron(patron_id, book_id)
        
        # Check database directly
        conn = get_db_connection()
        record = conn.execute('''
            SELECT return_date FROM borrow_records 
            WHERE patron_id = ? AND book_id = ?
            ORDER BY id DESC LIMIT 1
        ''', (patron_id, book_id)).fetchone()
        conn.close()
        
        assert record is not None
        assert record['return_date'] is not None
    
    def test_return_book_negative_book_id(self, sample_patron_id):
        """Test with negative book_id"""
        success, message = return_book_by_patron(sample_patron_id, -1)
        
        assert success is False
        assert "Book not found" in message
    
    def test_return_book_zero_book_id(self, sample_patron_id):
        """Test with book_id = 0"""
        success, message = return_book_by_patron(sample_patron_id, 0)
        
        assert success is False
        assert "Book not found" in message
    
    def test_return_book_multiple_sequential_returns_different_patrons(self):
        """Test multiple patrons can return copies of same book"""
        # Setup: Add book with 3 copies
        add_book_to_catalog("Multi-Copy Book", "Author", "8888888888888", 3)
        book = get_book_by_isbn("8888888888888")
        assert book is not None, "Book should be found after adding to catalog"
        book_id = book['id']
        
        patrons = ["111111", "222222", "333333"]
        
        # All borrow
        for patron_id in patrons:
            borrow_book_by_patron(patron_id, book_id)
        
        # All return sequentially
        for patron_id in patrons:
            success, _ = return_book_by_patron(patron_id, book_id)
            assert success is True
        
        # Check final availability
        book_final = get_book_by_id(book_id)
        assert book_final is not None, "Book should exist after returns"
        assert book_final['available_copies'] == 3


# ============================================================================
# Test Class: calculate_late_fee_for_book() - AI Generated
# ============================================================================

class TestCalculateLateFeeForBookAI:
    """AI-Generated comprehensive tests for late fee calculation"""
    
    def test_late_fee_on_time_no_fee(self, borrowed_book_setup):
        """Book not yet due - should have $0 fee"""
        patron_id, book_id = borrowed_book_setup
        
        result = calculate_late_fee_for_book(patron_id, book_id)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'On time'
    
    @pytest.mark.parametrize("days_overdue,expected_fee", OVERDUE_FEE_CALCULATIONS)
    def test_late_fee_various_overdue_periods(self, sample_patron_id, sample_book_id, days_overdue, expected_fee):
        """Parameterized test for different overdue periods"""
        # Setup: Borrow and make overdue
        borrow_book_by_patron(sample_patron_id, sample_book_id)
        
        conn = get_db_connection()
        past_due = (datetime.now() - timedelta(days=days_overdue)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due, sample_patron_id, sample_book_id))
        conn.commit()
        conn.close()
        
        result = calculate_late_fee_for_book(sample_patron_id, sample_book_id)
        
        assert result['fee_amount'] == expected_fee
        assert result['days_overdue'] == days_overdue
        assert result['status'] == 'Overdue'
    
    def test_late_fee_exactly_due_date_not_overdue(self, sample_patron_id, sample_book_id):
        """Book due exactly now - should not be overdue yet"""
        borrow_book_by_patron(sample_patron_id, sample_book_id)
        
        conn = get_db_connection()
        exactly_now = datetime.now().isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (exactly_now, sample_patron_id, sample_book_id))
        conn.commit()
        conn.close()
        
        result = calculate_late_fee_for_book(sample_patron_id, sample_book_id)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'On time'
    
    def test_late_fee_extreme_overdue_100_days(self, sample_patron_id, sample_book_id):
        """Test extreme overdue scenario (100+ days)"""
        borrow_book_by_patron(sample_patron_id, sample_book_id)
        
        conn = get_db_connection()
        past_due = (datetime.now() - timedelta(days=100)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due, sample_patron_id, sample_book_id))
        conn.commit()
        conn.close()
        
        result = calculate_late_fee_for_book(sample_patron_id, sample_book_id)
        
        assert result['fee_amount'] == 50.00  # 100 * 0.50
        assert result['days_overdue'] == 100
    
    def test_late_fee_no_active_borrow_record(self, sample_patron_id, sample_book_id):
        """Patron never borrowed the book"""
        result = calculate_late_fee_for_book(sample_patron_id, sample_book_id)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'No active borrow record'
    
    @pytest.mark.parametrize("invalid_id,reason", INVALID_PATRON_IDS)
    def test_late_fee_invalid_patron_ids(self, invalid_id, reason, sample_book_id):
        """Test late fee with various invalid patron IDs"""
        result = calculate_late_fee_for_book(invalid_id, sample_book_id)
        
        assert result['fee_amount'] == 0.00
        assert result['status'] == 'Invalid patron ID'
    
    def test_late_fee_calculation_precision(self, sample_patron_id, sample_book_id):
        """Verify fee calculation precision: days * 0.50"""
        days = 13
        borrow_book_by_patron(sample_patron_id, sample_book_id)
        
        conn = get_db_connection()
        past_due = (datetime.now() - timedelta(days=days)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due, sample_patron_id, sample_book_id))
        conn.commit()
        conn.close()
        
        result = calculate_late_fee_for_book(sample_patron_id, sample_book_id)
        
        expected_fee = days * 0.50
        assert result['fee_amount'] == expected_fee
        assert abs(result['fee_amount'] - expected_fee) < 0.01  # Floating point precision
    
    def test_late_fee_does_not_modify_database(self, overdue_book_setup):
        """Verify late fee calculation doesn't modify database state"""
        patron_id, book_id = overdue_book_setup
        
        # Get initial state
        conn = get_db_connection()
        initial_record = conn.execute('''
            SELECT * FROM borrow_records 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (patron_id, book_id)).fetchone()
        conn.close()
        
        # Calculate fee
        calculate_late_fee_for_book(patron_id, book_id)
        
        # Verify no change
        conn = get_db_connection()
        after_record = conn.execute('''
            SELECT * FROM borrow_records 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (patron_id, book_id)).fetchone()
        conn.close()
        
        assert dict(initial_record) == dict(after_record)
    
    def test_late_fee_negative_book_id(self, sample_patron_id):
        """Test with negative book_id"""
        result = calculate_late_fee_for_book(sample_patron_id, -999)
        
        assert result['fee_amount'] == 0.00
        assert result['status'] == 'No active borrow record'
    
    def test_late_fee_return_dict_keys(self, sample_patron_id, sample_book_id):
        """Verify returned dictionary contains all required keys"""
        result = calculate_late_fee_for_book(sample_patron_id, sample_book_id)
        
        assert 'fee_amount' in result
        assert 'days_overdue' in result
        assert 'status' in result
        assert isinstance(result['fee_amount'], float)
        assert isinstance(result['days_overdue'], int)
        assert isinstance(result['status'], str)


# ============================================================================
# Test Class: search_books_in_catalog() - AI Generated
# ============================================================================

class TestSearchBooksInCatalogAI:
    """AI-Generated comprehensive tests for book search functionality"""
    
    def test_search_title_case_insensitive_match(self):
        """Search by title with different cases"""
        results_lower = search_books_in_catalog("gatsby", "title")
        results_upper = search_books_in_catalog("GATSBY", "title")
        results_mixed = search_books_in_catalog("GaTsBY", "title")
        
        assert len(results_lower) >= 1
        assert len(results_upper) >= 1
        assert len(results_mixed) >= 1
        assert results_lower[0]['title'] == results_upper[0]['title']
    
    def test_search_author_case_insensitive_match(self):
        """Search by author with different cases"""
        results = search_books_in_catalog("orwell", "author")
        
        assert len(results) >= 1
        assert any("Orwell" in book['author'] for book in results)
    
    def test_search_isbn_exact_match_required(self):
        """ISBN search requires exact match"""
        exact = search_books_in_catalog("9780743273565", "isbn")
        partial = search_books_in_catalog("97807432", "isbn")
        
        assert len(exact) == 1
        assert len(partial) == 0
    
    def test_search_title_partial_substring_match(self):
        """Partial string in title should match"""
        results = search_books_in_catalog("Great", "title")
        
        assert len(results) >= 1
        assert any("Great" in book['title'] for book in results)
    
    @pytest.mark.parametrize("search_term,search_type,expected_count,should_find", SEARCH_SCENARIOS)
    def test_search_parameterized_scenarios(self, search_term, search_type, expected_count, should_find):
        """Parameterized tests for various search scenarios"""
        results = search_books_in_catalog(search_term, search_type)
        
        if should_find:
            assert len(results) >= expected_count
        else:
            assert len(results) == expected_count
    
    def test_search_invalid_search_type(self):
        """Invalid search_type returns empty list"""
        invalid_types = ["invalid", "genre", "publication_year", "", "TITLE"]
        
        for invalid_type in invalid_types:
            results = search_books_in_catalog("test", invalid_type)
            assert results == []
            assert isinstance(results, list)
    
    def test_search_empty_search_term(self):
        """Empty search term returns empty list"""
        results = search_books_in_catalog("", "title")
        
        assert results == []
    
    def test_search_whitespace_only_term(self):
        """Whitespace-only search term returns empty list"""
        results = search_books_in_catalog("   ", "title")
        
        assert results == []
    
    def test_search_no_matches_returns_empty_list(self):
        """Search with no matches returns empty list"""
        results = search_books_in_catalog("XyZnOnExIsTeNt12345", "title")
        
        assert results == []
        assert isinstance(results, list)
    
    def test_search_multiple_matches_all_returned(self):
        """When multiple books match, all are returned"""
        # Add multiple books with "Python" in title
        add_book_to_catalog("Python Programming", "Author A", "1111111111111", 1)
        add_book_to_catalog("Learning Python", "Author B", "2222222222222", 1)
        add_book_to_catalog("Python Cookbook", "Author C", "3333333333333", 1)
        
        results = search_books_in_catalog("Python", "title")
        
        assert len(results) >= 3
        assert all("Python" in book['title'] for book in results)
    
    def test_search_special_characters_in_term(self):
        """Search with special characters"""
        # Add book with special characters
        add_book_to_catalog("C++ Programming!", "Author", "4444444444444", 1)
        
        results = search_books_in_catalog("C++", "title")
        
        # Should handle special characters in search
        assert len(results) >= 1
    
    def test_search_numeric_search_term(self):
        """Search with numeric string"""
        # Add book with number in title
        add_book_to_catalog("Python 3.9 Guide", "Author", "5555555555555", 1)
        
        results = search_books_in_catalog("3.9", "title")
        
        assert len(results) >= 1
    
    def test_search_very_long_search_term(self):
        """Search with very long string (200+ characters)"""
        long_term = "A" * 250
        
        results = search_books_in_catalog(long_term, "title")
        
        # Should handle gracefully, return empty
        assert results == []
    
    def test_search_returns_list_of_dicts(self):
        """Verify search returns list of dictionaries"""
        results = search_books_in_catalog("gatsby", "title")
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert isinstance(results[0], dict)
            assert 'title' in results[0]
            assert 'author' in results[0]
            assert 'isbn' in results[0]
    
    def test_search_does_not_modify_catalog(self):
        """Verify search doesn't modify database"""
        books_before = get_all_books()
        
        search_books_in_catalog("test", "title")
        
        books_after = get_all_books()
        
        assert len(books_before) == len(books_after)
    
    def test_search_author_partial_last_name(self):
        """Search by partial last name"""
        results = search_books_in_catalog("Lee", "author")
        
        assert len(results) >= 1
        assert any("Lee" in book['author'] for book in results)
    
    def test_search_performance_with_many_books(self):
        """Test search performance with larger catalog"""
        # Add 50 books
        for i in range(50):
            isbn = f"{1000000000000 + i}"
            add_book_to_catalog(f"Book {i}", f"Author {i}", isbn, 1)
        
        import time
        start = time.time()
        results = search_books_in_catalog("Book", "title")
        elapsed = time.time() - start
        
        # Should complete quickly (under 1 second)
        assert elapsed < 1.0
        assert len(results) >= 50


# ============================================================================
# Test Class: get_patron_status_report() - AI Generated
# ============================================================================

class TestGetPatronStatusReportAI:
    """AI-Generated comprehensive tests for patron status reports"""
    
    def test_patron_status_no_borrowed_books(self):
        """Patron with no borrowed books"""
        # Use a unique patron ID that hasn't borrowed anything
        patron_id = "999999"
        report = get_patron_status_report(patron_id)
        
        assert report['status'] == 'Valid patron'
        assert report['patron_id'] == patron_id
        assert report['total_books_borrowed'] == 0
        assert report['total_late_fees'] == 0.00
        assert len(report['borrowed_books']) == 0
    
    def test_patron_status_one_book_on_time(self):
        """Patron with one book, not overdue"""
        # Use unique patron ID for this test
        patron_id = "111111"
        book_id = 1
        borrow_book_by_patron(patron_id, book_id)
        
        report = get_patron_status_report(patron_id)
        
        assert report['total_books_borrowed'] == 1
        assert report['total_late_fees'] == 0.00
        assert len(report['borrowed_books']) == 1
        assert report['borrowed_books'][0]['is_overdue'] is False
    
    def test_patron_status_one_book_overdue(self):
        """Patron with one overdue book"""
        # Use unique patron ID for this test
        patron_id = "222222"
        book_id = 1
        borrow_book_by_patron(patron_id, book_id)
        
        # Make it overdue
        conn = get_db_connection()
        past_due = (datetime.now() - timedelta(days=10)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due, patron_id, book_id))
        conn.commit()
        conn.close()
        
        report = get_patron_status_report(patron_id)
        
        assert report['total_books_borrowed'] == 1
        assert report['total_late_fees'] == 5.00  # 10 days * $0.50
        assert report['borrowed_books'][0]['is_overdue'] is True
        assert report['borrowed_books'][0]['late_fee'] == 5.00
    
    def test_patron_status_multiple_books_mixed_status(self):
        """Patron with multiple books, some overdue"""
        patron_id = "111111"
        
        # Add books
        add_book_to_catalog("Book A", "Author", "7777777777777", 5)
        add_book_to_catalog("Book B", "Author", "8888888888888", 5)
        
        book_a = get_book_by_isbn("7777777777777")
        book_b = get_book_by_isbn("8888888888888")
        assert book_a is not None, "Book A should be found after adding to catalog"
        assert book_b is not None, "Book B should be found after adding to catalog"
        
        # Borrow multiple books
        borrow_book_by_patron(patron_id, 1)  # On time
        borrow_book_by_patron(patron_id, book_a['id'])  # Will be overdue
        borrow_book_by_patron(patron_id, book_b['id'])  # On time
        
        # Make one overdue
        conn = get_db_connection()
        past_due = (datetime.now() - timedelta(days=5)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due, patron_id, book_a['id']))
        conn.commit()
        conn.close()
        
        report = get_patron_status_report(patron_id)
        
        assert report['total_books_borrowed'] == 3
        assert report['total_late_fees'] == 2.50  # 5 days * $0.50
        
        overdue_count = sum(1 for b in report['borrowed_books'] if b['is_overdue'])
        assert overdue_count == 1
    
    def test_patron_status_all_books_overdue(self):
        """Patron with all books overdue"""
        patron_id = "222222"
        
        # Borrow two books
        borrow_book_by_patron(patron_id, 1)
        borrow_book_by_patron(patron_id, 2)
        
        # Make both overdue
        conn = get_db_connection()
        past_due_1 = (datetime.now() - timedelta(days=10)).isoformat()
        past_due_2 = (datetime.now() - timedelta(days=5)).isoformat()
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due_1, patron_id, 1))
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due_2, patron_id, 2))
        
        conn.commit()
        conn.close()
        
        report = get_patron_status_report(patron_id)
        
        assert report['total_books_borrowed'] == 2
        assert report['total_late_fees'] == 7.50  # (10*0.50) + (5*0.50)
        assert all(b['is_overdue'] for b in report['borrowed_books'])
    
    @pytest.mark.parametrize("invalid_id,reason", INVALID_PATRON_IDS)
    def test_patron_status_invalid_patron_ids(self, invalid_id, reason):
        """Test status report with various invalid patron IDs"""
        report = get_patron_status_report(invalid_id)
        
        assert report['status'] == 'Invalid patron ID'
    
    def test_patron_status_total_fees_matches_sum(self):
        """Verify total_late_fees equals sum of individual late fees"""
        patron_id = "333333"
        
        # Borrow three books
        borrow_book_by_patron(patron_id, 1)
        borrow_book_by_patron(patron_id, 2)
        
        add_book_to_catalog("Extra Book", "Author", "9999999999999", 1)
        book = get_book_by_isbn("9999999999999")
        assert book is not None, "Book should be found after adding to catalog"
        borrow_book_by_patron(patron_id, book['id'])
        
        # Make them overdue with different amounts
        conn = get_db_connection()
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', ((datetime.now() - timedelta(days=10)).isoformat(), patron_id, 1))
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', ((datetime.now() - timedelta(days=5)).isoformat(), patron_id, 2))
        
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', ((datetime.now() - timedelta(days=3)).isoformat(), patron_id, book['id']))
        
        conn.commit()
        conn.close()
        
        report = get_patron_status_report(patron_id)
        
        # Calculate sum manually
        individual_sum = sum(b['late_fee'] for b in report['borrowed_books'])
        
        assert report['total_late_fees'] == individual_sum
        assert report['total_late_fees'] == 9.00  # (10+5+3)*0.50
    
    def test_patron_status_date_format_validation(self, borrowed_book_setup):
        """Verify dates are formatted as YYYY-MM-DD strings"""
        patron_id, book_id = borrowed_book_setup
        
        report = get_patron_status_report(patron_id)
        
        book_info = report['borrowed_books'][0]
        
        # Should be strings
        assert isinstance(book_info['borrow_date'], str)
        assert isinstance(book_info['due_date'], str)
        
        # Should parse as dates
        borrow_date = datetime.strptime(book_info['borrow_date'], "%Y-%m-%d")
        due_date = datetime.strptime(book_info['due_date'], "%Y-%m-%d")
        
        # Due date should be 14 days after borrow date
        assert (due_date - borrow_date).days == 14
    
    def test_patron_status_book_due_today_not_overdue(self, sample_patron_id, sample_book_id):
        """Book due exactly today should not be marked overdue"""
        borrow_book_by_patron(sample_patron_id, sample_book_id)
        
        # Set due date to exactly today
        conn = get_db_connection()
        today = datetime.now().replace(hour=23, minute=59, second=59).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (today, sample_patron_id, sample_book_id))
        conn.commit()
        conn.close()
        
        report = get_patron_status_report(sample_patron_id)
        
        # Should not be overdue yet
        assert report['borrowed_books'][0]['is_overdue'] is False
        assert report['borrowed_books'][0]['late_fee'] == 0.00
    
    def test_patron_status_at_borrowing_limit(self):
        """Patron with maximum allowed books (5)"""
        patron_id = "444444"
        
        # Add extra books
        for i in range(5):
            isbn = f"{6000000000000 + i}"
            add_book_to_catalog(f"Limit Book {i}", "Author", isbn, 1)
        
        # Borrow 5 books (at limit)
        borrow_book_by_patron(patron_id, 1)
        borrow_book_by_patron(patron_id, 2)
        
        for i in range(3):
            isbn = f"{6000000000000 + i}"
            book = get_book_by_isbn(isbn)
            assert book is not None, "Book should be found after adding to catalog"
            borrow_book_by_patron(patron_id, book['id'])
        
        report = get_patron_status_report(patron_id)
        
        assert report['total_books_borrowed'] == 5
    
    def test_patron_status_returned_books_not_included(self):
        """Returned books should not appear in status report"""
        patron_id = "555555"
        
        # Borrow two books
        borrow_book_by_patron(patron_id, 1)
        borrow_book_by_patron(patron_id, 2)
        
        # Return one
        return_book_by_patron(patron_id, 1)
        
        report = get_patron_status_report(patron_id)
        
        # Should only show 1 active borrow
        assert report['total_books_borrowed'] == 1
        assert len(report['borrowed_books']) == 1
        assert report['borrowed_books'][0]['title'] != "The Great Gatsby"


# ============================================================================
# Integration Tests - AI Generated
# ============================================================================

class TestIntegrationScenariosAI:
    """AI-Generated integration tests for complete workflows"""
    
    def test_complete_library_lifecycle(self):
        """Complete lifecycle: Add books, borrow, check status, return"""
        # Add books with enough copies
        for i in range(5):
            isbn = f"{9000000000000 + i}"
            add_book_to_catalog(f"Integration Book {i}", f"Author {i}", isbn, 5)
        
        # Use unique patron IDs for this test
        patrons = ["777777", "888888", "999000"]
        
        # Each patron borrows 2 different books
        for idx, patron_id in enumerate(patrons):
            # Borrow first integration book
            isbn1 = f"{9000000000000 + idx}"
            book1 = get_book_by_isbn(isbn1)
            assert book1 is not None, "Book1 should be found after adding to catalog"
            borrow_book_by_patron(patron_id, book1['id'])
            
            # Borrow second integration book
            isbn2 = f"{9000000000000 + idx + 1}"
            book2 = get_book_by_isbn(isbn2)
            assert book2 is not None, "Book2 should be found after adding to catalog"
            borrow_book_by_patron(patron_id, book2['id'])
        
        # Check status for all - each should have 2 books
        for patron_id in patrons:
            report = get_patron_status_report(patron_id)
            assert report['total_books_borrowed'] == 2
        
        # Return all books
        for idx, patron_id in enumerate(patrons):
            isbn1 = f"{9000000000000 + idx}"
            book1 = get_book_by_isbn(isbn1)
            assert book1 is not None, "Book1 should be found after adding to catalog"
            return_book_by_patron(patron_id, book1['id'])
            
            isbn2 = f"{9000000000000 + idx + 1}"
            book2 = get_book_by_isbn(isbn2)
            assert book2 is not None, "Book2 should be found after adding to catalog"
            return_book_by_patron(patron_id, book2['id'])
        
        # Verify final state - all should have 0 books
        for patron_id in patrons:
            report = get_patron_status_report(patron_id)
            assert report['total_books_borrowed'] == 0
    
    def test_search_borrow_return_workflow(self):
        """Realistic user workflow: Search, borrow, return"""
        # Search for book
        results = search_books_in_catalog("Mockingbird", "title")
        assert len(results) >= 1
        
        book_id = results[0]['id']
        patron_id = "777777"
        
        # Borrow found book
        borrow_success, _ = borrow_book_by_patron(patron_id, book_id)
        assert borrow_success is True
        
        # Check status
        status = get_patron_status_report(patron_id)
        assert status['total_books_borrowed'] == 1
        
        # Calculate fee (should be 0)
        fee = calculate_late_fee_for_book(patron_id, book_id)
        assert fee['fee_amount'] == 0.00
        
        # Return
        return_success, _ = return_book_by_patron(patron_id, book_id)
        assert return_success is True
    
    def test_concurrent_borrow_and_return_operations(self):
        """Test data integrity with concurrent-like operations"""
        # Add book with multiple copies
        add_book_to_catalog("Concurrent Book", "Author", "5550000000000", 3)
        book = get_book_by_isbn("5550000000000")
        assert book is not None, "Book should be found after adding to catalog"
        book_id = book['id']
        
        # Three patrons borrow simultaneously
        patrons = ["111111", "222222", "333333"]
        for patron_id in patrons:
            borrow_book_by_patron(patron_id, book_id)
        
        # Check book availability
        book_check = get_book_by_id(book_id)
        assert book_check is not None, "Book should exist in database"
        assert book_check['available_copies'] == 0
        
        # Two patrons return
        return_book_by_patron(patrons[0], book_id)
        return_book_by_patron(patrons[1], book_id)
        
        # Check availability updated correctly
        book_after = get_book_by_id(book_id)
        assert book_after is not None, "Book should exist in database"
        assert book_after['available_copies'] == 2
    
    def test_data_integrity_no_duplicate_returns(self):
        """Verify return doesn't create duplicate records"""
        patron_id = "888888"
        book_id = 1
        
        # Borrow and return
        borrow_book_by_patron(patron_id, book_id)
        return_book_by_patron(patron_id, book_id)
        
        # Check database for single return record
        conn = get_db_connection()
        count = conn.execute('''
            SELECT COUNT(*) as cnt FROM borrow_records 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NOT NULL
        ''', (patron_id, book_id)).fetchone()['cnt']
        conn.close()
        
        assert count == 1  # Only one return record


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
