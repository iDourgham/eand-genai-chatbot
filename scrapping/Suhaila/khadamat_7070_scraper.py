import json
from bs4 import BeautifulSoup
import re

def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned

def scrape_7070_services():
    """Scrape the HTML content and extract service information"""
    
    # Read HTML content from file
    try:
        with open('Khadamat 7070/page_content.txt', 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print("Error: page_content.txt file not found. Please save the HTML content to page_content.txt")
        return
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open('Khadamat 7070/page_content.txt', 'r', encoding='latin-1') as file:
            html_content = file.read()
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize the main data structure
    scraped_data = {
        "url": "https://www.eand.com.eg/StaticFiles/portal2/etisalat/pages/services/etisalat_directory_7070.html",
        "title": "خدمات 7070",
        "description": "",
        "service_tagline": "",
        "service_features": {
            "section_title": "",
            "services": []
        }
    }
    
    # Extract main page title and description
    title_section = soup.find('section', class_='page_title_test')
    if title_section:
        # Extract main title
        main_title = title_section.find('h1')
        if main_title:
            scraped_data["title"] = clean_text(main_title.get_text())
        
        # Extract main description
        description_paragraphs = title_section.find_all('p', class_='fs-14')
        descriptions = []
        for p in description_paragraphs:
            desc_text = clean_text(p.get_text())
            if desc_text:
                descriptions.append(desc_text)
        
        if descriptions:
            scraped_data["description"] = " ".join(descriptions)
        
        # Extract header service text
        header_service = title_section.find('h5', class_='header-service')
        if header_service:
            scraped_data["service_tagline"] = clean_text(header_service.get_text())
    
    # Extract service features section title - FIXED THIS PART
    features_section = soup.find('div', class_='for__sectionTitles')
    if features_section:
        feature_titles = features_section.find_all('h3')
        scraped_data["service_features"]["section_title"] = " ".join([clean_text(title.get_text()) for title in feature_titles])
    
    # Extract individual service cards
    card_container = soup.find('div', class_='card-container')
    if card_container:
        service_cards = card_container.find_all('div', class_='card')
        
        for card in service_cards:
            service_info = {}
            
            # Extract service title
            title_tag = card.find('h5')
            if title_tag:
                service_info["title"] = clean_text(title_tag.get_text())
            
            # Extract service description
            desc_paragraph = card.find('p', class_='mt-30')
            if desc_paragraph:
                service_info["description"] = clean_text(desc_paragraph.get_text())
            
            # Only add if we have at least a title
            if service_info.get("title"):
                scraped_data["service_features"]["services"].append(service_info)
    
    # Extract mobile app section (if present and not entertainment)
    app_section = soup.find('section', class_='for__mobileApp')
    if app_section:
        app_info = {}
        
        
    # Save to JSON file
    output_filename = 'Khadamat 7070/e&_7070_services.json'
    try:
        with open(output_filename, 'w', encoding='utf-8') as json_file:
            json.dump(scraped_data, json_file, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")
        return None
    
    return scraped_data

def display_scraped_data(data):
    """Display the scraped data in a readable format"""
    if not data:
        return

if __name__ == "__main__":
    # Scrape the data
    scraped_data = scrape_7070_services()
    
    if scraped_data:
        # Display summary
        display_scraped_data(scraped_data)
        print("Scraping completed successfully!")
    else:
        print("Scraping failed.")