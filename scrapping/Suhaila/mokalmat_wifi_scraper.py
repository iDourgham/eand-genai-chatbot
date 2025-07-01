from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Any

def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned

def extract_terms_and_conditions(soup):
    """Extract terms and conditions from the page"""
    terms = []
    
    # Find the terms section
    terms_section = soup.find('section', id='for_features_and_terms')
    if terms_section:
        # Find all paragraph elements with terms
        term_divs = terms_section.find_all('div', class_=re.compile(r'col-.*my-3'))
        
        for div in term_divs:
            p_tag = div.find('p')
            if p_tag and p_tag.get_text(strip=True):
                text = clean_text(p_tag.get_text())

                if 'تطبق الشروط والأحكام' not in text:
                    terms.append(text)
    
    return terms


def extract_service_steps(soup):
    """Extract general service activation steps"""
    steps = []
    
    steps_sections = soup.find_all('section', id='for_programSteps')
    if steps_sections:
        # Get the last section which contains the activation steps
        last_section = steps_sections[-1]
        step_divs = last_section.find_all('div', class_=re.compile(r'col-.*my-3'))
        
        for div in step_divs:
            p_tag = div.find('p')
            if p_tag:
                text = clean_text(p_tag.get_text())
                if text:
                    steps.append(text)
    
    return steps

def extract_notes(soup):
    """Extract notes section"""
    notes = []
    
    # Find the notes section
    notes_sections = soup.find_all('section', id='for_programSteps')
    if len(notes_sections) >= 2:
        # The first section with this ID is the notes section
        notes_section = notes_sections[0]
        note_divs = notes_section.find_all('div', class_=re.compile(r'col-.*my-3'))
        
        for div in note_divs:
            p_tag = div.find('p')
            if p_tag:
                text = clean_text(p_tag.get_text())
                if text:
                    notes.append(text)
    
    return notes

def extract_phone_compatibility(soup) -> Dict[str, Any]:
    """
    Extract phone compatibility information from HTML table and return structured data
    """
    # Find the table with phone compatibility data
    table = soup.find('table', class_='table table-bordered border-radius-20 mt-30')
    
    if not table:
        print("Phone compatibility table not found")
        return {}
    
    # Extract headers
    headers = []
    header_row = table.find('thead')
    if header_row:
        tr_title = header_row.find('tr', id='trTitle')
        if tr_title:
            for th in tr_title.find_all('th'):
                header_text = th.get_text(strip=True)
                headers.append(header_text)
    
    # Extract phone data
    phones_by_brand = {}
    tbody = table.find('tbody', id='devices')
    
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= len(headers):
                for i, cell in enumerate(cells[:len(headers)]):
                    if i < len(headers):
                        brand = headers[i]
                        phone_text = cell.get_text(strip=True)
                        
                        # Clean up phone text - remove extra whitespace and Arabic text
                        phone_text = re.sub(r'\s+', ' ', phone_text)
                        phone_text = phone_text.replace('قريباً', '').strip()  # Remove "coming soon" text
                        
                        if phone_text and phone_text not in ['', 'n']:
                            if brand not in phones_by_brand:
                                phones_by_brand[brand] = []
                            
                            # Check if phone already exists to avoid duplicates
                            if phone_text not in phones_by_brand[brand]:
                                phones_by_brand[brand].append(phone_text)
    
    # Create structured phone compatibility data
    phone_compatibility = {
        "compatible_phones_by_brand": phones_by_brand,
        "compatibility_summary": {
            "total_brands": len(phones_by_brand),
            "total_phones": sum(len(phones) for phones in phones_by_brand.values()),
            "phone_counts_by_brand": {brand: len(phones) for brand, phones in phones_by_brand.items()}
        }
    }
    
    return phone_compatibility

def scrape_wifi_calling_page():
    """Main scraping function that combines all data extraction"""
    
    # Read HTML file
    try:
        with open('Mokalmat Wifi/page_content.txt', 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print("Error: file not found. Please make sure the file exists.")
        return None
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract page title
    title_h1 = soup.find('h1', class_='GESSTwoBold_font')
    page_title = clean_text(title_h1.get_text()) if title_h1 else "مكالمات Wi-Fi"
    
    # Extract service description
    description_p = soup.find('p', class_='fs-14 grey-color')
    service_description = clean_text(description_p.get_text()) if description_p else ""
    
    # Extract different sections
    terms_conditions = extract_terms_and_conditions(soup)
    activation_steps = extract_service_steps(soup)
    notes = extract_notes(soup)
    phone_compatibility = extract_phone_compatibility(soup)
    
    
    # Structure all extracted data into comprehensive JSON
    extracted_data = {
        "page_info": {
            "url": "https://www.eand.com.eg/StaticFiles/portal2/etisalat/pages/services/wifi_calling.html",
            "title": page_title,
            "description": service_description,
        },
        "service_details": {
            "terms_and_conditions": terms_conditions,
            "activation_steps": activation_steps,
            "important_notes": notes
        },
        "phone_compatibility": phone_compatibility
    }
    
    return extracted_data

def save_to_json(data, filename):
    """Save extracted data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f"Data successfully saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False

def search_phone_in_data(data, phone_model: str) -> List[str]:
    """Search for a specific phone model across all brands"""
    matching_phones = []
    
    if "phone_compatibility" in data and "compatible_phones_by_brand" in data["phone_compatibility"]:
        phones_data = data["phone_compatibility"]["compatible_phones_by_brand"]
        
        for brand, phones in phones_data.items():
            for phone in phones:
                if phone_model.lower() in phone.lower():
                    matching_phones.append(f"{brand}: {phone}")
    
    return matching_phones

def get_brand_phones_from_data(data, brand_name: str) -> List[str]:
    """Get all phones for a specific brand"""
    if "phone_compatibility" in data and "compatible_phones_by_brand" in data["phone_compatibility"]:
        phones_data = data["phone_compatibility"]["compatible_phones_by_brand"]
        
        for brand, phones in phones_data.items():
            if brand_name.lower() in brand.lower():
                return phones
    
    return []

def main():
    """Main execution function"""
    print("Starting comprehensive Wi-Fi Calling page scraping...")
    print("="*60)
    
    # Extract all data
    extracted_data = scrape_wifi_calling_page()
    
    if extracted_data:
        # Save to main JSON file only
        filename = "Mokalmat Wifi/e&_mokalmat_wifi.json"
        if save_to_json(extracted_data, filename):
            print(f"Successfully extracted and saved all data to {filename}")
        else:
            print("Failed to save data to JSON file")
    else:
        print("Failed to extract data from HTML file")

if __name__ == "__main__":
    main()