# Website Scraper

A robust web scraping tool built with Selenium that automatically extracts product information from 1stDibs.com, a high-end furniture and art marketplace.

## Features

- **Multi-Category Support**: Scrapes products from different categories including:
  - Lighting
  - Seating
  - Tables
  - Storage
  - Custom URLs

- **Comprehensive Data Collection**:
  - Product names and descriptions
  - Pricing information
  - High-quality product images
  - Detailed specifications
  - Creator/designer information
  - Product URLs and IDs

- **Robust Error Handling**:
  - Handles dynamic content loading
  - Manages cookie consent popups
  - Recovers from common web scraping issues
  - Saves error states for debugging

- **Data Organization**:
  - Saves data in JSON format
  - Creates individual product files
  - Maintains separate files for listings and detailed product information
  - Includes timestamps in filenames for version control

## Prerequisites

- Python 3.x
- Chrome browser installed
- Required Python packages:
  - selenium
  - webdriver_manager

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install selenium webdriver_manager
```

## Usage

Run the script with default settings (Lighting category, 2 pages):
```bash
python selenium_base.py
```

Or import and use the function in your code:
```python
from selenium_base import scrape_1stdibs

# Scrape specific category (1-4) and number of pages
scrape_1stdibs(category_option="1", max_pages=5)
```

### Category Options
1. Lighting
2. Seating
3. Tables
4. Storage

## Output

The scraper creates the following directory structure:
```
scraped_data/
├── products/
│   └── product_[ID]_[timestamp].json
├── 1stdibs_[category]_listings_[timestamp].json
├── 1stdibs_[category]_detailed_[timestamp].json
├── 1stdibs_[category]_listings_[timestamp]_complete.json
└── 1stdibs_[category]_detailed_[timestamp]_complete.json
```

### Data Format

Each product JSON file contains:
- Basic product information (name, price, URL)
- Detailed product description
- Product specifications
- High-resolution image URLs
- Raw data for reference

## Features

- **Anti-Detection Measures**: Implements various techniques to avoid being detected as a bot
- **Pagination Handling**: Automatically navigates through multiple pages
- **Progress Tracking**: Saves data after each page to prevent data loss
- **User Interaction**: Allows manual intervention when needed
- **Browser Management**: Option to keep browser open for inspection

## Error Handling

The scraper includes comprehensive error handling for:
- Network issues
- Missing elements
- Dynamic content loading
- Invalid sessions
- Click interception
- Stale elements

## Notes

- The scraper respects website load times and includes appropriate delays
- It's recommended to use this tool responsibly and in accordance with 1stDibs' terms of service
- The script includes built-in rate limiting to avoid overwhelming the server
- Debug information is saved when errors occur

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. 