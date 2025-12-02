"""
End-to-End Testing for Library Management System
Uses Selenium WebDriver for browser automation with proper waits and assertions

Test Requirements:
- Two realistic user flows: Add Book and Borrow Book
- Real browser session (Chrome)
- Explicit waits for element interactions
- Clear assertions on UI elements and text
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


# Configuration
BASE_URL = "http://localhost:5000"
DEFAULT_TIMEOUT = 10  # 10 seconds


@pytest.fixture(scope="function")
def driver():
    """Create a new Chrome WebDriver instance for each test."""
    import os
    import stat
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")
    
    # Get ChromeDriver path and fix the path issue on macOS ARM
    driver_path = ChromeDriverManager().install()
    # If the path points to the wrong file, find the correct chromedriver executable
    if 'THIRD_PARTY_NOTICES' in driver_path:
        driver_dir = os.path.dirname(driver_path)
        driver_path = os.path.join(driver_dir, 'chromedriver')
    
    # Make sure the driver is executable
    if os.path.exists(driver_path):
        os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(DEFAULT_TIMEOUT)
    
    yield driver
    
    driver.quit()


class TestAddBookFlow:
    """Test Flow 1: Add a new book to the catalog"""
    
    def test_add_book_complete_flow(self, driver):
        """
        E2E Test: Add a new book and verify it appears in catalog
        
        Steps:
        1. Navigate to catalog page
        2. Click "Add New Book" button
        3. Fill in book details (title, author, ISBN, copies)
        4. Submit the form
        5. Verify redirect to catalog
        6. Verify the new book appears in the catalog with correct details
        """
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
        
        # Step 1: Navigate to catalog
        driver.get(f"{BASE_URL}/catalog")
        assert "/catalog" in driver.current_url
        h2 = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
        assert "Book Catalog" in h2.text
        
        # Step 2: Click "Add New Book" button
        add_book_link = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "➕ Add New Book"))
        )
        add_book_link.click()
        
        # Verify we're on the add book page
        wait.until(EC.url_contains("/add_book"))
        h2 = driver.find_element(By.TAG_NAME, "h2")
        assert "Add New Book" in h2.text
        
        # Step 3: Fill in book details with unique ISBN
        unique_isbn = f"978074327{int(time.time()) % 10000:04d}"
        
        title_input = wait.until(EC.presence_of_element_located((By.ID, "title")))
        title_input.send_keys("The Catcher in the Rye")
        
        author_input = driver.find_element(By.ID, "author")
        author_input.send_keys("J.D. Salinger")
        
        isbn_input = driver.find_element(By.ID, "isbn")
        isbn_input.send_keys(unique_isbn)
        
        copies_input = driver.find_element(By.ID, "total_copies")
        copies_input.send_keys("5")
        
        # Step 4: Submit the form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Step 5: Verify redirect to catalog
        wait.until(EC.url_contains("/catalog"))
        
        # Wait for success message
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "flash-success"))
        )
        assert "successfully" in success_message.text.lower() or "added" in success_message.text.lower()
        
        # Step 6: Verify the new book appears in catalog
        # Wait for the table to be visible
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Find the row containing our new book
        page_source = driver.page_source
        assert "The Catcher in the Rye" in page_source
        assert "J.D. Salinger" in page_source
        assert unique_isbn in page_source
        assert "5/5 Available" in page_source
        
        print(f"✅ Successfully added book with ISBN {unique_isbn} and verified in catalog")


class TestBorrowBookFlow:
    """Test Flow 2: Borrow a book from the catalog"""
    
    def test_borrow_book_complete_flow(self, driver):
        """
        E2E Test: Borrow an available book and verify confirmation
        
        Steps:
        1. Navigate to catalog page
        2. Identify an available book
        3. Enter patron ID in the borrow form
        4. Submit the borrow request
        5. Verify success message appears
        6. Verify available copies decreased by 1
        """
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
        
        # Step 1: Navigate to catalog
        driver.get(f"{BASE_URL}/catalog")
        assert "/catalog" in driver.current_url
        h2 = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
        assert "Book Catalog" in h2.text
        
        # Step 2: Find an available book
        # Wait for catalog table to load
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Look for a book with "Available" status
        available_books = driver.find_elements(By.CSS_SELECTOR, "tr")
        available_book_row = None
        
        for row in available_books:
            if "Available" in row.text and "/5 Available" in row.text:
                available_book_row = row
                break
        
        assert available_book_row is not None, "No available books found"
        
        # Get the first available book's details
        cells = available_book_row.find_elements(By.TAG_NAME, "td")
        book_title = cells[1].text
        book_author = cells[2].text
        availability_text = cells[4].text
        
        # Extract current availability (e.g., "3/5 Available" -> 3)
        current_available = int(availability_text.split("/")[0])
        total_copies = int(availability_text.split("/")[1].split()[0])
        
        print(f"📚 Found available book: {book_title} by {book_author}")
        print(f"   Current availability: {current_available}/{total_copies}")
        
        # Step 3: Fill in patron ID
        patron_id = "123456"
        patron_input = available_book_row.find_element(By.NAME, "patron_id")
        patron_input.send_keys(patron_id)
        
        # Step 4: Submit borrow request
        borrow_button = available_book_row.find_element(By.CSS_SELECTOR, "button[type='submit']")
        borrow_button.click()
        
        # Wait for page to reload
        wait.until(EC.url_contains("/catalog"))
        time.sleep(1)  # Brief wait for page to fully load
        
        # Step 5: Verify success message
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "flash-success"))
        )
        assert "borrow" in success_message.text.lower() or "success" in success_message.text.lower()
        
        print(f"✅ Success message displayed: '{success_message.text}'")
        
        # Step 6: Verify available copies decreased
        # Find the same book again and check its availability
        page_source = driver.page_source
        expected_available = current_available - 1
        
        if expected_available > 0:
            # Should still show as available but with fewer copies
            expected_text = f"{expected_available}/{total_copies} Available"
            assert expected_text in page_source
            print(f"✅ Available copies decreased from {current_available} to {expected_available}")
        else:
            # Should now show as "Not Available"
            assert "Not Available" in page_source
            print(f"✅ Book is now marked as 'Not Available' (all copies borrowed)")
        
        print(f"✅ Successfully borrowed '{book_title}' for patron {patron_id}")


class TestAddAndBorrowCombinedFlow:
    """Test Flow 3: Combined test - Add a book then immediately borrow it"""
    
    def test_add_then_borrow_book(self, driver):
        """
        E2E Test: Add a new book with 2 copies and borrow one
        
        This test combines both flows to ensure they work together:
        1. Add a new book with 2 copies
        2. Borrow one copy
        3. Verify availability shows 1/2 Available
        """
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
        
        # Part 1: Add a new book
        driver.get(f"{BASE_URL}/add_book")
        h2 = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
        assert "Add New Book" in h2.text
        
        unique_isbn = f"978019953{int(time.time()) % 100000:05d}"
        test_title = "Test Book for E2E"
        test_author = "Test Author"
        
        title_input = driver.find_element(By.ID, "title")
        title_input.send_keys(test_title)
        
        author_input = driver.find_element(By.ID, "author")
        author_input.send_keys(test_author)
        
        isbn_input = driver.find_element(By.ID, "isbn")
        isbn_input.send_keys(unique_isbn)
        
        copies_input = driver.find_element(By.ID, "total_copies")
        copies_input.send_keys("2")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Verify book added
        wait.until(EC.url_contains("/catalog"))
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "flash-success"))
        )
        
        # Verify it shows 2/2 Available initially
        page_source = driver.page_source
        assert test_title in page_source
        assert test_author in page_source
        assert "2/2 Available" in page_source
        
        # Part 2: Borrow the newly added book
        # Find all rows and locate our test book
        rows = driver.find_elements(By.CSS_SELECTOR, "tr")
        test_book_row = None
        
        for row in rows:
            if test_title in row.text and test_author in row.text:
                test_book_row = row
                break
        
        assert test_book_row is not None, "Test book not found in catalog"
        
        # Borrow one copy
        patron_input = test_book_row.find_element(By.NAME, "patron_id")
        patron_input.send_keys("999888")
        
        borrow_button = test_book_row.find_element(By.CSS_SELECTOR, "button[type='submit']")
        borrow_button.click()
        
        # Wait for page reload
        wait.until(EC.url_contains("/catalog"))
        time.sleep(1)
        
        # Part 3: Verify availability is now 1/2
        page_source = driver.page_source
        assert "1/2 Available" in page_source
        
        print(f"✅ Successfully added '{test_title}' and borrowed 1 copy")
        print(f"✅ Availability correctly shows 1/2 Available")
