"""
Assignment 3 - Test Suite for Payment Gateway Integration
Tests pay_late_fees() and refund_late_fee_payment() using mocking and stubbing techniques.

This test suite demonstrates:
1. Stubbing database functions to provide fake data without verification
2. Mocking PaymentGateway class to verify interactions and method calls
3. Comprehensive test coverage of positive, negative, and edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from services.library_service import pay_late_fees, refund_late_fee_payment
from services.payment_service import PaymentGateway


# ============================================================================
# TEST SUITE FOR pay_late_fees() - 5 Required Test Cases
# ============================================================================

class TestPayLateFees:
    """Test suite for pay_late_fees() function using mocking and stubbing."""
    
    def test_pay_late_fees_successful_payment(self, mocker):
        """
        Positive Test: Successful payment processing
        
        Stubs Used:
        - calculate_late_fee_for_book: Returns fake late fee data ($10.50, 21 days overdue)
        - get_book_by_id: Returns fake book data
        
        Mocks Used:
        - PaymentGateway.process_payment: Mock to verify correct parameters passed
        
        Verification:
        - assert_called_once_with: Verify payment gateway called with correct patron_id, amount, description
        """
        # STUBBING: Stub database functions to return fake data
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 10.50,
                'days_overdue': 21,
                'status': 'Overdue'
            }
        )
        
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value={
                'id': 1,
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'isbn': '9780743273565'
            }
        )
        
        # MOCKING: Create mock payment gateway to verify interactions
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (
            True,  # success
            'txn_123456_1699564800',  # transaction_id
            'Payment of $10.50 processed successfully'  # message
        )
        
        # Execute the function
        success, message, transaction_id = pay_late_fees('123456', 1, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is True
        assert 'Payment successful!' in message
        assert transaction_id == 'txn_123456_1699564800'
        
        # MOCK VERIFICATION: Verify payment gateway was called correctly
        mock_gateway.process_payment.assert_called_once_with(
            patron_id='123456',
            amount=10.50,
            description="Late fees for 'The Great Gatsby'"
        )
    
    def test_pay_late_fees_payment_declined(self, mocker):
        """
        Negative Test: Payment declined by gateway
        
        Stubs Used:
        - calculate_late_fee_for_book: Returns fake late fee data
        - get_book_by_id: Returns fake book data
        
        Mocks Used:
        - PaymentGateway.process_payment: Mock returns failure response
        
        Verification:
        - assert_called_once: Verify payment gateway was called exactly once
        """
        # STUBBING: Stub database functions
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 1500.00,
                'days_overdue': 3000,
                'status': 'Overdue'
            }
        )
        
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value={
                'id': 2,
                'title': '1984',
                'author': 'George Orwell',
                'isbn': '9780451524935'
            }
        )
        
        # MOCKING: Create mock that simulates payment decline
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (
            False,  # success = False
            '',  # no transaction_id
            'Payment declined: amount exceeds limit'  # error message
        )
        
        # Execute the function
        success, message, transaction_id = pay_late_fees('654321', 2, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Payment failed:' in message
        assert 'amount exceeds limit' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was called
        mock_gateway.process_payment.assert_called_once()
    
    def test_pay_late_fees_invalid_patron_id(self, mocker):
        """
        Negative Test: Invalid patron ID - should NOT call payment gateway
        
        Stubs Used: None (validation happens before database access)
        
        Mocks Used:
        - PaymentGateway.process_payment: Mock should NOT be called
        
        Verification:
        - assert_not_called: Verify payment gateway was NEVER called for invalid input
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with invalid patron ID (not 6 digits)
        success, message, transaction_id = pay_late_fees('12345', 1, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Invalid patron ID' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was NOT called
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_zero_fees(self, mocker):
        """
        Edge Case Test: Zero late fees - should NOT call payment gateway
        
        Stubs Used:
        - calculate_late_fee_for_book: Returns zero fee amount
        
        Mocks Used:
        - PaymentGateway.process_payment: Mock should NOT be called
        
        Verification:
        - assert_not_called: Verify payment gateway not called when no fees exist
        """
        # STUBBING: Stub to return zero late fees
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 0.00,
                'days_overdue': 0,
                'status': 'On time'
            }
        )
        
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute the function
        success, message, transaction_id = pay_late_fees('123456', 1, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'No late fees to pay' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was NOT called
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_network_error_exception(self, mocker):
        """
        Exception Test: Network error during payment processing
        
        Stubs Used:
        - calculate_late_fee_for_book: Returns fake late fee data
        - get_book_by_id: Returns fake book data
        
        Mocks Used:
        - PaymentGateway.process_payment: Mock raises exception
        
        Verification:
        - assert_called_once: Verify payment gateway was called before exception
        """
        # STUBBING: Stub database functions
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 5.00,
                'days_overdue': 10,
                'status': 'Overdue'
            }
        )
        
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value={
                'id': 3,
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'isbn': '9780061120084'
            }
        )
        
        # MOCKING: Create mock that raises network error exception
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.side_effect = ConnectionError('Network timeout')
        
        # Execute the function
        success, message, transaction_id = pay_late_fees('789012', 3, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Payment processing error' in message
        assert 'Network timeout' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was called
        mock_gateway.process_payment.assert_called_once()


# ============================================================================
# TEST SUITE FOR refund_late_fee_payment() - 5 Required Test Cases
# ============================================================================

class TestRefundLateFeePayment:
    """Test suite for refund_late_fee_payment() function using mocking."""
    
    def test_refund_late_fee_payment_successful(self, mocker):
        """
        Positive Test: Successful refund processing
        
        Stubs Used: None (no database interaction in this function)
        
        Mocks Used:
        - PaymentGateway.refund_payment: Mock to verify correct parameters
        
        Verification:
        - assert_called_once_with: Verify refund called with correct transaction_id and amount
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (
            True,  # success
            'Refund of $7.50 processed successfully. Refund ID: refund_txn_123_1699564800'
        )
        
        # Execute the function
        success, message = refund_late_fee_payment('txn_123456_1699564800', 7.50, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is True
        assert 'Refund of $7.50 processed successfully' in message
        
        # MOCK VERIFICATION: Verify refund gateway called with correct parameters
        mock_gateway.refund_payment.assert_called_once_with('txn_123456_1699564800', 7.50)
    
    def test_refund_late_fee_payment_invalid_transaction_id(self, mocker):
        """
        Negative Test: Invalid transaction ID format
        
        Stubs Used: None
        
        Mocks Used:
        - PaymentGateway.refund_payment: Mock should NOT be called
        
        Verification:
        - assert_not_called: Verify refund not called for invalid transaction ID
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with invalid transaction ID (doesn't start with 'txn_')
        success, message = refund_late_fee_payment('invalid_id_12345', 5.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Invalid transaction ID' in message
        
        # MOCK VERIFICATION: Verify refund gateway was NOT called
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_late_fee_payment_negative_amount(self, mocker):
        """
        Negative Test: Negative refund amount
        
        Stubs Used: None
        
        Mocks Used:
        - PaymentGateway.refund_payment: Mock should NOT be called
        
        Verification:
        - assert_not_called: Verify refund not called for invalid amount
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with negative amount
        success, message = refund_late_fee_payment('txn_123456_1699564800', -10.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Refund amount must be greater than 0' in message
        
        # MOCK VERIFICATION: Verify refund gateway was NOT called
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_late_fee_payment_zero_amount(self, mocker):
        """
        Edge Case Test: Zero refund amount
        
        Stubs Used: None
        
        Mocks Used:
        - PaymentGateway.refund_payment: Mock should NOT be called
        
        Verification:
        - assert_not_called: Verify refund not called for zero amount
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with zero amount
        success, message = refund_late_fee_payment('txn_789012_1699564800', 0.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Refund amount must be greater than 0' in message
        
        # MOCK VERIFICATION: Verify refund gateway was NOT called
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_late_fee_payment_exceeds_maximum(self, mocker):
        """
        Boundary Test: Refund amount exceeds $15 maximum late fee
        
        Stubs Used: None
        
        Mocks Used:
        - PaymentGateway.refund_payment: Mock should NOT be called
        
        Verification:
        - assert_not_called: Verify refund not called when amount exceeds maximum
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with amount exceeding maximum ($15.00)
        success, message = refund_late_fee_payment('txn_111222_1699564800', 20.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'exceeds maximum late fee' in message
        
        # MOCK VERIFICATION: Verify refund gateway was NOT called
        mock_gateway.refund_payment.assert_not_called()


# ============================================================================
# ADDITIONAL TEST CASES FOR COMPREHENSIVE COVERAGE
# ============================================================================

class TestPayLateFeesCoverageEnhancement:
    """Additional tests to improve code coverage for pay_late_fees()."""
    
    def test_pay_late_fees_book_not_found(self, mocker):
        """
        Edge Case: Book ID not found in database
        
        Tests the branch where get_book_by_id returns None
        """
        # STUBBING: Stub to return valid late fee but book not found
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'fee_amount': 5.00,
                'days_overdue': 10,
                'status': 'Overdue'
            }
        )
        
        mocker.patch(
            'services.library_service.get_book_by_id',
            return_value=None  # Book not found
        )
        
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute the function
        success, message, transaction_id = pay_late_fees('123456', 999, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Book not found' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was NOT called
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_missing_fee_amount_key(self, mocker):
        """
        Edge Case: calculate_late_fee_for_book returns dict without 'fee_amount' key
        
        Tests error handling when fee calculation returns unexpected format
        """
        # STUBBING: Stub to return incomplete fee info
        mocker.patch(
            'services.library_service.calculate_late_fee_for_book',
            return_value={
                'status': 'Error'
                # Missing 'fee_amount' key
            }
        )
        
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute the function
        success, message, transaction_id = pay_late_fees('123456', 1, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Unable to calculate late fees' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was NOT called
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_empty_patron_id(self, mocker):
        """
        Negative Test: Empty patron ID string
        
        Tests validation with empty string instead of invalid format
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with empty patron ID
        success, message, transaction_id = pay_late_fees('', 1, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Invalid patron ID' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was NOT called
        mock_gateway.process_payment.assert_not_called()
    
    def test_pay_late_fees_non_numeric_patron_id(self, mocker):
        """
        Negative Test: Non-numeric patron ID
        
        Tests validation with letters in patron ID
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with non-numeric patron ID
        success, message, transaction_id = pay_late_fees('ABC123', 1, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Invalid patron ID' in message
        assert transaction_id is None
        
        # MOCK VERIFICATION: Verify payment gateway was NOT called
        mock_gateway.process_payment.assert_not_called()


class TestRefundLateFeePaymentCoverageEnhancement:
    """Additional tests to improve code coverage for refund_late_fee_payment()."""
    
    def test_refund_late_fee_payment_gateway_failure(self, mocker):
        """
        Negative Test: Payment gateway returns failure
        
        Tests the branch where refund_payment returns (False, error_message)
        """
        # MOCKING: Create mock that returns failure
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (
            False,  # success = False
            'Transaction not found'
        )
        
        # Execute the function
        success, message = refund_late_fee_payment('txn_999999_1699564800', 5.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Refund failed:' in message
        assert 'Transaction not found' in message
        
        # MOCK VERIFICATION: Verify refund gateway was called
        mock_gateway.refund_payment.assert_called_once_with('txn_999999_1699564800', 5.00)
    
    def test_refund_late_fee_payment_exception_handling(self, mocker):
        """
        Exception Test: Payment gateway raises exception during refund
        
        Tests exception handling in refund_late_fee_payment()
        """
        # MOCKING: Create mock that raises exception
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.side_effect = RuntimeError('API service unavailable')
        
        # Execute the function
        success, message = refund_late_fee_payment('txn_123456_1699564800', 5.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Refund processing error' in message
        assert 'API service unavailable' in message
        
        # MOCK VERIFICATION: Verify refund gateway was called
        mock_gateway.refund_payment.assert_called_once()
    
    def test_refund_late_fee_payment_empty_transaction_id(self, mocker):
        """
        Negative Test: Empty transaction ID
        
        Tests validation with empty string
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with empty transaction ID
        success, message = refund_late_fee_payment('', 5.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'Invalid transaction ID' in message
        
        # MOCK VERIFICATION: Verify refund gateway was NOT called
        mock_gateway.refund_payment.assert_not_called()
    
    def test_refund_late_fee_payment_boundary_valid_amount(self, mocker):
        """
        Boundary Test: Refund exactly $15.00 (maximum allowed)
        
        Tests the boundary condition at exactly $15.00
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.refund_payment.return_value = (
            True,
            'Refund of $15.00 processed successfully. Refund ID: refund_txn_max_1699564800'
        )
        
        # Execute with maximum allowed amount
        success, message = refund_late_fee_payment('txn_123456_1699564800', 15.00, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is True
        assert 'Refund of $15.00 processed successfully' in message
        
        # MOCK VERIFICATION: Verify refund gateway was called
        mock_gateway.refund_payment.assert_called_once_with('txn_123456_1699564800', 15.00)
    
    def test_refund_late_fee_payment_boundary_just_over_maximum(self, mocker):
        """
        Boundary Test: Refund $15.01 (just over maximum)
        
        Tests the boundary condition just above $15.00
        """
        # MOCKING: Create mock payment gateway
        mock_gateway = Mock(spec=PaymentGateway)
        
        # Execute with amount just over maximum
        success, message = refund_late_fee_payment('txn_123456_1699564800', 15.01, mock_gateway)
        
        # ASSERTIONS: Verify function behavior
        assert success is False
        assert 'exceeds maximum late fee' in message
        
        # MOCK VERIFICATION: Verify refund gateway was NOT called
        mock_gateway.refund_payment.assert_not_called()


# ============================================================================
# TEST COVERAGE FOR calculate_late_fee_for_book() (Supplementary)
# ============================================================================

class TestCalculateLateFeeForBook:
    """
    Supplementary tests for calculate_late_fee_for_book() to improve overall coverage.
    This function is stubbed in payment tests but needs its own coverage.
    """
    
    def test_calculate_late_fee_invalid_patron_id(self, mocker):
        """Test calculate_late_fee_for_book with invalid patron ID."""
        from services.library_service import calculate_late_fee_for_book
        
        # Test with invalid patron ID
        result = calculate_late_fee_for_book('12345', 1)  # Only 5 digits
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'Invalid patron ID'
    
    def test_calculate_late_fee_no_borrow_record(self, mocker):
        """Test calculate_late_fee_for_book when no borrow record exists."""
        from services.library_service import calculate_late_fee_for_book
        
        # STUBBING: Stub to return empty borrowed books list
        mocker.patch(
            'services.library_service.get_patron_borrowed_books',
            return_value=[]  # No borrowed books
        )
        
        result = calculate_late_fee_for_book('123456', 999)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'No active borrow record'
    
    def test_calculate_late_fee_on_time_return(self, mocker):
        """Test calculate_late_fee_for_book when book is returned on time."""
        from services.library_service import calculate_late_fee_for_book
        
        # STUBBING: Stub to return borrow record with future due date
        future_date = datetime.now() + timedelta(days=7)
        mocker.patch(
            'services.library_service.get_patron_borrowed_books',
            return_value=[{
                'book_id': 1,
                'title': 'Test Book',
                'author': 'Test Author',
                'borrow_date': datetime.now() - timedelta(days=7),
                'due_date': future_date,  # Due date is in the future
                'is_overdue': False
            }]
        )
        
        result = calculate_late_fee_for_book('123456', 1)
        
        assert result['fee_amount'] == 0.00
        assert result['days_overdue'] == 0
        assert result['status'] == 'On time'
    
    def test_calculate_late_fee_overdue_calculation(self, mocker):
        """Test calculate_late_fee_for_book with overdue book."""
        from services.library_service import calculate_late_fee_for_book
        
        # STUBBING: Stub to return borrow record with past due date (10 days overdue)
        past_date = datetime.now() - timedelta(days=10)
        mocker.patch(
            'services.library_service.get_patron_borrowed_books',
            return_value=[{
                'book_id': 2,
                'title': 'Overdue Book',
                'author': 'Test Author',
                'borrow_date': datetime.now() - timedelta(days=24),
                'due_date': past_date,  # Due date was 10 days ago
                'is_overdue': True
            }]
        )
        
        result = calculate_late_fee_for_book('123456', 2)
        
        # Should be $0.50 per day * 10 days = $5.00
        assert result['fee_amount'] == 5.00
        assert result['days_overdue'] == 10
        assert result['status'] == 'Overdue'
