import os
import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException, InvalidSessionIdException
from webdriver_manager.chrome import ChromeDriverManager

def extract_product_id(url):
    """Extract product ID from product URL"""
    match = re.search(r'/id-([^/]+)/?', url)
    if match:
        return match.group(1)
    return None

def scrape_product_details(driver, product_url, product_id, base_data):
    """Scrape detailed information from a product page"""
    print(f"Visiting product page: {product_url}")
    try:
        driver.get(product_url)
        time.sleep(3)  # Allow page to load
        
        # Skip if we don't have required fields
        if not product_id or not product_url:
            print("Missing product ID or URL - skipping")
            return None
            
        # Initialize product data with base information from the listing page
        product_data = {
            "retailer": "1stDibs",
            "product_id": product_id,
            "name": base_data.get("name", ""),
            "slug": product_id,
            "price": base_data.get("price", ""),
            "description": "",
            "image_url": base_data.get("image_url", ""),
            "url": product_url,
            "specifications": {},
            "raw_data": {
                "productId": product_id,
                "slug": product_id,
                "url": product_url,
                "name": base_data.get("name", ""),
                "price": base_data.get("price", ""),
                "imageUrl": base_data.get("image_url", ""),
                "description": "",
                "specifications": {},
                "jsonLd": None,
                "extractionMethod": "automated"
            }
        }
        
        # Extract description
        description_selectors = [
            "div[data-tn='listing-page-description']",
            "div.product-description",
            "div.description",
            "#description"
        ]
        
        for selector in description_selectors:
            try:
                desc_element = driver.find_element(By.CSS_SELECTOR, selector)
                description = desc_element.text
                if description:
                    product_data["description"] = description
                    product_data["raw_data"]["description"] = description
                    break
            except:
                continue
        
        # Extract specifications/details
        specs = {}
        
        # Try to find specification tables or lists
        spec_section_selectors = [
            "div[data-tn='listing-page-details']",
            "div.product-details",
            "section.specifications",
            "table.details"
        ]
        
        for selector in spec_section_selectors:
            try:
                # Look for detail labels and values
                spec_section = driver.find_element(By.CSS_SELECTOR, selector)
                
                # Try to find structured specification data
                try:
                    # Look for dt/dd pairs
                    labels = spec_section.find_elements(By.CSS_SELECTOR, "dt")
                    values = spec_section.find_elements(By.CSS_SELECTOR, "dd")
                    
                    for i in range(min(len(labels), len(values))):
                        label = labels[i].text.strip().lower().replace(" ", "_")
                        value = values[i].text.strip()
                        if label and value:
                            specs[label] = value
                except:
                    # Try alternative format with div pairs or table rows
                    try:
                        rows = spec_section.find_elements(By.CSS_SELECTOR, "tr, .specification-row")
                        for row in rows:
                            try:
                                label_elem = row.find_element(By.CSS_SELECTOR, "th, .label, .spec-label")
                                value_elem = row.find_element(By.CSS_SELECTOR, "td, .value, .spec-value")
                                
                                label = label_elem.text.strip().lower().replace(" ", "_")
                                value = value_elem.text.strip()
                                if label and value:
                                    specs[label] = value
                            except:
                                continue
                    except:
                        pass
                
                # If we found at least some specifications, break
                if specs:
                    break
                    
            except:
                continue
        
        # Add creator to specifications if available from listing
        if base_data.get("creator") and base_data.get("creator") != "":
            specs["creator"] = base_data.get("creator")
        
        # Update specifications in product data
        product_data["specifications"] = specs
        product_data["raw_data"]["specifications"] = specs
        
        # Get higher quality image if available
        image_selectors = [
            "img[data-tn='listing-page-hero-image']",
            ".product-image-main img",
            ".main-image img",
            "div.gallery img"
        ]
        
        for selector in image_selectors:
            try:
                img_element = driver.find_element(By.CSS_SELECTOR, selector)
                image_url = img_element.get_attribute("src")
                if image_url and "width=" in image_url:
                    # Try to increase the image size by modifying URL parameter
                    product_data["image_url"] = image_url.replace("width=240", "width=1200")
                    product_data["raw_data"]["imageUrl"] = image_url.replace("width=240", "width=1200")
                    break
            except:
                continue
        
        # Validate that we have required fields before returning
        if not product_data["name"]:
            print(f"Product {product_id} missing name - skipping")
            return None
            
        if not product_data["image_url"]:
            print(f"Product {product_id} missing image - skipping")
            return None
        
        return product_data
    except Exception as e:
        print(f"Error extracting product details: {str(e)}")
        return None

def is_valid_listing(listing_data):
    """Check if a listing has the required fields"""
    required_fields = ["name", "url", "image_url", "price", "product_id"]
    for field in required_fields:
        if not listing_data.get(field):
            return False
    return True

def scrape_1stdibs(category_option=None, max_pages=None):
    """Scrape data from 1stdibs.com"""
    print("Starting scraper for 1stdibs products...")
    
    # Set up Chrome options for stability
    chrome_options = Options()
    
    # Add a user agent to mimic a regular browser
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Add additional arguments to enhance stability and avoid detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-browser-side-navigation')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # Define available categories
        category_options = {
            "1": {"name": "Lighting", "url": "https://www.1stdibs.com/furniture/lighting/"},
            "2": {"name": "Seating", "url": "https://www.1stdibs.com/furniture/seating/"},
            "3": {"name": "Tables", "url": "https://www.1stdibs.com/furniture/tables/"},
            "4": {"name": "Storage", "url": "https://www.1stdibs.com/furniture/storage-case-pieces/"}
        }
        
        # Use provided category or default to lighting (1)
        if category_option is None:
            print("Available categories:")
            for key, value in category_options.items():
                print(f"{key}. {value['name']}")
            
            category_choice = input("Enter the number of the category to scrape (1-4), or enter a full URL [default: 1]: ") or "1"
        else:
            category_choice = category_option
        
        if category_choice in category_options:
            category_url = category_options[category_choice]["url"]
            category_name = category_options[category_choice]["name"].lower()
        else:
            category_url = category_choice if "://" in category_choice else "https://www.1stdibs.com/furniture/lighting/"
            category_name = "products"
        
        # Navigate to the target URL
        print(f"Navigating to {category_url}")
        driver.get(category_url)
        
        # Handle cookie consent if it appears
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookie_button.click()
            print("Cookie consent popup handled.")
        except:
            print("No cookie consent popup detected or failed to handle it.")
        
        # Create directories to store the scraped data
        os.makedirs('scraped_data', exist_ok=True)
        os.makedirs('scraped_data/products', exist_ok=True)
        
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize empty list for all scraped data
        all_product_listings = []
        detailed_products = []
        current_page = 1
        has_next_page = True
        
        # Continue scraping while there are more pages and we haven't hit max_pages limit
        while has_next_page and (max_pages is None or current_page <= max_pages):
            print(f"\n--- Processing Page {current_page} ---")
            
            # Add a pause to allow JavaScript to load
            time.sleep(5)
            
            # Scroll down to trigger lazy loading
            for _ in range(4):
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(1)
            
            # Try several selector patterns to find product listings
            selectors = [
                "div[data-tn='item-tile-wrapper']",
                "div.item-tile-wrapper",
                "div[data-component='ItemTile']",
                "li.product-grid-item",
                "div.productTile",
                "article.productCard"
            ]
            
            products_found = False
            product_tiles = []
            
            for selector in selectors:
                try:
                    print(f"Trying selector: {selector}")
                    # Check if elements are present
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 0:
                        product_tiles = elements
                        products_found = True
                        print(f"Found {len(product_tiles)} products with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Error with selector {selector}: {str(e)}")
            
            if not products_found:
                print("Could not find product listings with any of the tried selectors.")
                # Save page source for debugging
                with open(f"page_source_page{current_page}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                
                # Try to find any relevant HTML structure
                print("Scanning page for potential product elements...")
                search_terms = ["product", "item", "tile", "card", "listing"]
                for term in search_terms:
                    elements = driver.find_elements(By.XPATH, f"//*[contains(@class, '{term}') or contains(@data-tn, '{term}')]")
                    if elements and len(elements) > 0:
                        print(f"Found {len(elements)} potential elements containing '{term}' in class or data attributes")
                
                # Ask the user if they want to continue scraping
                continue_scraping = input(f"No product listings found on page {current_page}. Do you want to continue with manual analysis? (y/n): ")
                if continue_scraping.lower() != 'y':
                    print("Scraping terminated by user.")
                    break
            
            # If we have product tiles, proceed with scraping
            page_listings = []
            page_details = []
            
            if products_found:
                print(f"Starting to scrape {len(product_tiles)} product listings...")
                
                # Iterate through each product tile
                for i, tile in enumerate(product_tiles, 1):
                    try:
                        print(f"Scraping listing {i} of {len(product_tiles)}...")
                        
                        listing_data = {}
                        
                        # Try different selectors for product name
                        name_selectors = [
                            "h2", 
                            "h3", 
                            "a[data-tn='item-tile-title-anchor']", 
                            ".title", 
                            "[data-tn='product-title']"
                        ]
                        
                        product_name = ""
                        for selector in name_selectors:
                            try:
                                name_element = tile.find_element(By.CSS_SELECTOR, selector)
                                product_name = name_element.text
                                if product_name:
                                    break
                            except:
                                continue
                        
                        listing_data['name'] = product_name
                        
                        # Try different selectors for product URL
                        url_selectors = [
                            "a[data-tn='item-tile-title-anchor']",
                            "a[href*='/id-']",
                            "a.product-link",
                            "a:first-child"
                        ]
                        
                        product_link = ""
                        for selector in url_selectors:
                            try:
                                link_element = tile.find_element(By.CSS_SELECTOR, selector)
                                product_link = link_element.get_attribute("href")
                                if product_link:
                                    break
                            except:
                                continue
                        
                        listing_data['url'] = product_link
                        
                        # Try different selectors for product image URL
                        image_selectors = [
                            "img[data-tn='product-image']",
                            "img.product-image",
                            "img:first-child",
                            "[data-srcset]",
                            "[srcset]"
                        ]
                        
                        product_image = ""
                        for selector in image_selectors:
                            try:
                                img_element = tile.find_element(By.CSS_SELECTOR, selector)
                                product_image = img_element.get_attribute("src") or img_element.get_attribute("data-src") or img_element.get_attribute("srcset")
                                if product_image:
                                    break
                            except:
                                continue
                        
                        listing_data['image_url'] = product_image
                        
                        # Try different selectors for price
                        price_selectors = [
                            "div[data-tn='price']",
                            ".price",
                            "[data-tn='product-price']",
                            "span.money"
                        ]
                        
                        price = ""
                        for selector in price_selectors:
                            try:
                                price_element = tile.find_element(By.CSS_SELECTOR, selector)
                                price = price_element.text
                                if price:
                                    break
                            except:
                                continue
                        
                        listing_data['price'] = price
                        
                        # Try different selectors for creator/brand
                        creator_selectors = [
                            "a[data-tn='quick-view-creator-link']",
                            ".creator",
                            ".designer",
                            "[data-tn='product-creator']"
                        ]
                        
                        creator = ""
                        for selector in creator_selectors:
                            try:
                                creator_element = tile.find_element(By.CSS_SELECTOR, selector)
                                creator = creator_element.text
                                if creator:
                                    break
                            except:
                                continue
                        
                        listing_data['creator'] = creator
                        
                        # Extract product_id from URL
                        product_id = extract_product_id(product_link)
                        listing_data['product_id'] = product_id
                        
                        # Validate the listing data before processing further
                        if is_valid_listing(listing_data):
                            # Add valid listing to the current page data
                            page_listings.append(listing_data)
                            
                            # Visit product page and get detailed information
                            if product_link and product_id:
                                # Instead of opening in a new tab, just navigate to the page directly
                                # and then navigate back to the main page after scraping
                                current_url = driver.current_url
                                
                                # Get detailed product data
                                detailed_product = scrape_product_details(driver, product_link, product_id, listing_data)
                                
                                if detailed_product:
                                    page_details.append(detailed_product)
                                    
                                    # Save individual product file with consistent format
                                    filename = f"scraped_data/products/product_{product_id}_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')[:-3]}Z.json"
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(detailed_product, f, ensure_ascii=False, indent=2)
                                    print(f"Saved detailed product data to {filename}")
                                
                                # Go back to the main listing page
                                driver.get(current_url)
                                time.sleep(2)  # Wait for page to load
                        else:
                            print(f"Skipping listing {i} due to missing required data")
                    except Exception as e:
                        print(f"Error processing listing {i}: {str(e)}")
                        continue
            
            # Add only valid products to all lists
            all_product_listings.extend(page_listings)
            detailed_products.extend(page_details)
            
            # Save progress after each page
            with open(f'scraped_data/1stdibs_{category_name}_listings_{timestamp}.json', 'w', encoding='utf-8') as f:
                json.dump(all_product_listings, f, ensure_ascii=False, indent=4)
                
            with open(f'scraped_data/1stdibs_{category_name}_detailed_{timestamp}.json', 'w', encoding='utf-8') as f:
                json.dump(detailed_products, f, ensure_ascii=False, indent=4)
            
            print(f"Page {current_page} complete. {len(all_product_listings)} total product listings scraped so far.")
            print(f"{len(detailed_products)} detailed product pages scraped so far.")
            
            # If we've reached the max pages limit, stop
            if max_pages is not None and current_page >= max_pages:
                print(f"Reached the maximum number of pages ({max_pages}). Stopping.")
                break
                
            # Check for next page button
            try:
                # Scroll to the bottom of the page to make sure pagination is visible
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                next_button = None
                
                # Try different ways to find the next button
                next_button_selectors = [
                    "button[data-tn='page-forward']",
                    "a[data-tn='page-forward']",
                    "button.pagination-next",
                    "a.pagination-next",
                    "li.pagination-next > a",
                    "button[aria-label='Next Page']"
                ]
                
                for selector in next_button_selectors:
                    try:
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in next_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                next_button = btn
                                break
                        if next_button:
                            break
                    except:
                        continue
                
                if next_button and not "disabled" in next_button.get_attribute("class"):
                    print(f"Navigating to page {current_page + 1}...")
                    try:
                        # Try to click normally first
                        next_button.click()
                    except (ElementClickInterceptedException, StaleElementReferenceException):
                        # If normal click fails, try JavaScript click
                        driver.execute_script("arguments[0].click();", next_button)
                    
                    current_page += 1
                    time.sleep(3)  # Wait for page to load
                else:
                    print("No more pages available.")
                    has_next_page = False
            except Exception as e:
                print(f"Error navigating to next page: {str(e)}")
                # Save page source for debugging
                try:
                    with open(f"pagination_error_page{current_page}.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                except:
                    print("Could not save error page source.")
                
                # Ask if user wants to continue or stop
                continue_scraping = input("Error navigating to next page. Do you want to stop scraping? (y/n): ")
                if continue_scraping.lower() == 'y':
                    has_next_page = False
                else:
                    current_page += 1
        
        # Final save of all data
        with open(f'scraped_data/1stdibs_{category_name}_listings_{timestamp}_complete.json', 'w', encoding='utf-8') as f:
            json.dump(all_product_listings, f, ensure_ascii=False, indent=4)
            
        with open(f'scraped_data/1stdibs_{category_name}_detailed_{timestamp}_complete.json', 'w', encoding='utf-8') as f:
            json.dump(detailed_products, f, ensure_ascii=False, indent=4)
        
        print(f"Scraping complete.")
        print(f"{len(all_product_listings)} total valid product listings scraped.")
        print(f"{len(detailed_products)} detailed product pages scraped.")
        print(f"Basic listing data saved to scraped_data/1stdibs_{category_name}_listings_{timestamp}_complete.json")
        print(f"Detailed product data saved to scraped_data/1stdibs_{category_name}_detailed_{timestamp}_complete.json")
        print(f"Individual product files saved in scraped_data/products/ directory")
        
        # Ask the user if they want to close the browser
        close_browser = input("Do you want to close the browser? (y/n): ")
        if close_browser.lower() == 'y':
            driver.quit()
            print("Browser closed.")
        else:
            print("Browser left open. Remember to close it manually when you're done.")
    
    except InvalidSessionIdException:
        print("Browser session became invalid. The scraper will now exit.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Save page source for debugging
        try:
            with open("error_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()
        except:
            print("Could not save error page or close driver.")

if __name__ == "__main__":
    # Default to category 1 (Lighting) and limit to 2 pages for testing
    scrape_1stdibs(category_option="1", max_pages=2)