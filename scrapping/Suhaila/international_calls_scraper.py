from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Any

def clean_text(text: str) -> str:
    """Remove newlines and extra whitespace from text."""
    if not text:
        return ""
    # Replace newlines with spaces and clean up extra whitespace
    cleaned = re.sub(r'\n+', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def read_html_content(file_path: str) -> str:
    """Read HTML content from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File {file_path} not found. Attempting to fetch from URL...")
        return None

def extract_pricing_table(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract pricing information from the main pricing table."""
    pricing_data = {}
    
    # Find the pricing section
    pricing_section = soup.find('section', {'id': 'for_table'})
    if not pricing_section:
        return pricing_data
    
    # Extract zone prices
    table_rows = pricing_section.find_all('tr')
    zones = []
    prices = []
    
    for row in table_rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 1:
            text = clean_text(cells[0].get_text(strip=True))
            if 'zone' in text.lower() or 'htr' in text.lower():
                zones.append(text)
            elif 'جنيه/الدقيقة' in text:
                # Extract price value
                price_match = re.search(r'(\d+)\s*جنيه/الدقيقة', text)
                if price_match:
                    prices.append(int(price_match.group(1)))
    
    # Match zones with prices
    for i, zone in enumerate(zones):
        if i < len(prices):
            pricing_data[zone] = {
                'price_per_minute': prices[i],
                'currency': 'EGP'
            }
    
    return pricing_data

def extract_satellite_pricing(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract satellite pricing information."""
    satellite_data = {}
    
    # Find the satellite pricing section
    satellite_section = soup.find('section', {'id': 'for_textContainer'})
    if not satellite_section:
        return satellite_data
    
    # Extract section title from bundles-container
    section_title = ""
    bundles_container = satellite_section.find('div', class_='bundles-container')
    if bundles_container:
        title_div = bundles_container.find('div', class_='for__sectionTitles')
        if title_div:
            h3_tags = title_div.find_all('h3', class_='ff-suissintl-bold')
            titles = [clean_text(h3.get_text(strip=True)) for h3 in h3_tags]
            section_title = ' '.join(titles)
    
    # Extract service title from the text container
    service_title = ""
    title_container = satellite_section.find('div', class_='title')
    if title_container:
        h5_tags = title_container.find_all('h5', class_='ff-suissintl-bold')
        service_titles = [clean_text(h5.get_text(strip=True)) for h5 in h5_tags]
        service_title = ' '.join(service_titles)
    
    # Extract satellite services and prices - Multiple approaches for robustness
    services = {}
    
    # Method 1: Original approach - look for specific structure
    main_row = satellite_section.find('div', class_='row mt-30')
    if main_row:
        text_container = main_row.find('div', class_='text-container')
        if text_container:
            pricing_row = text_container.find('div', class_='row mt-3')
            if pricing_row:
                price_columns = pricing_row.find_all('div', class_='col-sm-12 col-md-6 col-lg-3')
                
                for col in price_columns:
                    h6_tag = col.find('h6', class_='ff-suissintl-bold')
                    p_tag = col.find('p', class_='mediumGrey-color')
                    
                    if h6_tag and p_tag:
                        price_text = clean_text(h6_tag.get_text(strip=True))
                        service_name = clean_text(p_tag.get_text(strip=True))
                        
                        # Extract price value
                        price_match = re.search(r'(\d+)\s*جنيه?/الدقيقة', price_text)
                        if price_match:
                            price_value = int(price_match.group(1))
                            services[service_name] = {
                                'price_per_minute': price_value,
                                'currency': 'EGP',
                                'full_price_text': price_text,
                                'service_type': 'satellite'
                            }
    
    # Method 2: Fallback - look for any h6 and p tags in the satellite section
    if not services:
        all_h6_tags = satellite_section.find_all('h6', class_='ff-suissintl-bold')
        all_p_tags = satellite_section.find_all('p', class_='mediumGrey-color')
        
        # Try to pair h6 tags with p tags
        for i, h6_tag in enumerate(all_h6_tags):
            price_text = clean_text(h6_tag.get_text(strip=True))
            
            # Look for price pattern
            if 'جنيه' in price_text and 'الدقيقة' in price_text:
                # Find corresponding service name
                service_name = ""
                
                # Try to find the next p tag after this h6
                next_p = h6_tag.find_next('p', class_='mediumGrey-color')
                if next_p:
                    service_name = clean_text(next_p.get_text(strip=True))
                elif i < len(all_p_tags):
                    service_name = clean_text(all_p_tags[i].get_text(strip=True))
                
                if service_name:
                    # Extract price value
                    price_match = re.search(r'(\d+)\s*جنيه?/الدقيقة', price_text)
                    if price_match:
                        price_value = int(price_match.group(1))
                        services[service_name] = {
                            'price_per_minute': price_value,
                            'currency': 'EGP',
                            'full_price_text': price_text,
                            'service_type': 'satellite'
                        }
    
    # Method 3: Most flexible - look for any pricing patterns in the section
    if not services:
        # Find all text that contains pricing information
        all_text_elements = satellite_section.find_all(text=True)
        price_texts = []
        service_names = []
        
        for text in all_text_elements:
            cleaned_text = clean_text(text)
            if cleaned_text:
                # Check if this text contains price information
                if 'جنيه' in cleaned_text and 'الدقيقة' in cleaned_text:
                    price_texts.append(cleaned_text)
                # Check if this could be a service name (not empty, not just numbers)
                elif cleaned_text and not re.match(r'^\d+$', cleaned_text) and len(cleaned_text) > 2:
                    # Skip common non-service texts
                    if cleaned_text not in ['أسعار', 'الستالايت', 'المناطق', 'صعب', 'الوصول', 'اليها']:
                        service_names.append(cleaned_text)
        
        # Try to extract services from the collected texts
        for price_text in price_texts:
            price_match = re.search(r'(\d+)\s*جنيه?/الدقيقة', price_text)
            if price_match:
                price_value = int(price_match.group(1))
                # Use a generic service name if we can't find specific ones
                service_key = f"satellite_service_{len(services) + 1}"
                services[service_key] = {
                    'price_per_minute': price_value,
                    'currency': 'EGP',
                    'full_price_text': price_text,
                    'service_type': 'satellite'
                }
    
    # Build complete satellite data structure
    satellite_data = {
        'section_title': section_title,
        'service_title': service_title,
        'services': services,
        'total_services': len(services),
        'service_category': 'satellite_and_remote_areas'
    }
    
    return satellite_data

def extract_kol_el_donia_service(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract 'Kol El Donia' (All The World) service information."""
    kol_el_donia_data = {}
    
    # Find sections with title containing "كل الدنيا"
    sections = soup.find_all('section', {'id': 'for_features_and_terms'})
    
    for section in sections:
        title_div = section.find('div', class_='for__sectionTitles')
        if title_div:
            h3_tags = title_div.find_all('h3')
            titles = [clean_text(h3.get_text(strip=True)) for h3 in h3_tags]
            
            if any('كل الدنيا' in title for title in titles):
                # Extract service features
                features = []
                paragraphs = section.find_all('p')
                
                for p in paragraphs:
                    text = clean_text(p.get_text(strip=True))
                    if text:
                        features.append(text)
                
                kol_el_donia_data = {
                    'service_name': 'كل الدنيا (All The World)',
                    'features': features,
                    'pricing_options': [
                        {
                            'type': 'per_call_fee',
                            'price_per_minute': 8,
                            'setup_fee': 4.5,
                            'currency': 'EGP',
                            'subscription_code': '1919'
                        },
                        {
                            'type': 'monthly_fee',
                            'price_per_minute': 8,
                            'monthly_fee': 30,
                            'currency': 'EGP',
                            'subscription_code': '1999'
                        }
                    ]
                }
                break
    
    return kol_el_donia_data

def extract_other_international_services(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract other international services pricing and full text content."""
    other_services = {}
    
    # Find sections with title containing "دوليه اخري"
    sections = soup.find_all('section', {'id': 'for_features_and_terms'})
    
    for section in sections:
        title_div = section.find('div', class_='for__sectionTitles')
        if title_div:
            h3_tags = title_div.find_all('h3')
            titles = [clean_text(h3.get_text(strip=True)) for h3 in h3_tags]
            
            if any('دوليه اخري' in title for title in titles):
                # Extract service title
                service_title = ' '.join(titles)
                
                # Extract all paragraphs content
                paragraphs = section.find_all('p')
                services_text = []
                
                for p in paragraphs:
                    text = clean_text(p.get_text(strip=True))
                    if text:
                        services_text.append(text)
                
                # Parse pricing information from text
                pricing_info = {}
                
                for text in services_text:
                    # Extract international SMS pricing
                    if 'الرسالة الدولية' in text:
                        price_match = re.search(r'(\d+)\s*جنيه?ا?', text)
                        if price_match:
                            pricing_info['international_sms'] = {
                                'price': int(price_match.group(1)),
                                'currency': 'EGP',
                                'service_type': 'SMS',
                                'full_text': text
                            }
                    
                    # Extract international MMS pricing  
                    elif 'الرسالة المصورة الدولية' in text:
                        price_match = re.search(r'(\d+)\s*جنيه?ا?', text)
                        if price_match:
                            pricing_info['international_mms'] = {
                                'price': int(price_match.group(1)),
                                'currency': 'EGP',
                                'service_type': 'MMS',
                                'full_text': text
                            }
                
                # Build the complete service data
                other_services = {
                    'service_title': service_title,
                    'full_content': services_text,
                    'pricing_details': pricing_info,
                    'services_count': len(services_text)
                }
                break
    
    return other_services

def extract_premium_international_numbers(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract premium international numbers information."""
    premium_data = {}
    
    # Find sections with title containing "الارقام الدولية المميزة"
    sections = soup.find_all('section', {'id': 'for_features_and_terms'})
    
    for section in sections:
        title_div = section.find('div', class_='for__sectionTitles')
        if title_div:
            h3_tags = title_div.find_all('h3')
            titles = [clean_text(h3.get_text(strip=True)) for h3 in h3_tags]
            
            if any('الارقام الدولية المميزة' in title for title in titles):
                # Extract price from title
                price_title = next((title for title in titles if 'جنية للدقيقة' in title), None)
                price_per_minute = 100  # Default based on the title
                
                if price_title:
                    price_match = re.search(r'(\d+)\s*جنية للدقيقة', price_title)
                    if price_match:
                        price_per_minute = int(price_match.group(1))
                
                # Extract service features
                features = []
                paragraphs = section.find_all('p')
                
                for p in paragraphs:
                    text = clean_text(p.get_text(strip=True))
                    if text:
                        features.append(text)
                
                premium_data = {
                    'service_name': 'الارقام الدولية المميزة (Premium International Numbers)',
                    'price_per_minute': price_per_minute,
                    'currency': 'EGP',
                    'features': features,
                    'services_included': ['مسابقات', 'استشارات طبية', 'وأكثر']
                }
                break
    
    return premium_data

def extract_zone_countries(soup: BeautifulSoup) -> Dict[str, List[str]]:
    """Extract countries for each zone."""
    zones_data = {}
    
    # Find all tab panes that contain zone information
    tab_panes = soup.find_all('div', class_='tab-pane')
    
    for pane in tab_panes:
        # Get zone name from tab or header
        zone_name = None
        
        # Try to find zone name in header
        header = pane.find('h6')
        if header:
            zone_text = clean_text(header.get_text(strip=True))
            if zone_text and zone_text != 'المنطقة':
                zone_name = zone_text
        
        # If not found in header, try tab id
        if not zone_name:
            pane_id = pane.get('id', '')
            if 'superSocial' in pane_id:
                zone_name = 'Zone 1'
            elif 'superVideo' in pane_id:
                zone_name = 'Zone 2'
            elif 'superGaming' in pane_id:
                zone_name = 'Zone 3'
            elif 'superMusic' in pane_id:
                zone_name = 'HTR 1'
            elif 'htr2' in pane_id:
                zone_name = 'HTR 2'
        
        if zone_name:
            countries = []
            # Find all table cells with country names
            table = pane.find('table')
            if table:
                cells = table.find_all('td')
                for cell in cells:
                    country = clean_text(cell.get_text(strip=True))
                    if country and country != '-' and country != 'المنطقة':
                        countries.append(country)
            
            if countries:
                zones_data[zone_name] = countries
    
    return zones_data

def extract_card_view_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract data from card view format."""
    card_data = {}
    
    # Find card sections
    cards = soup.find_all('div', class_='card')
    
    for card in cards:
        card_body = card.find('div', class_='card-body')
        if card_body:
            list_items = card_body.find_all('li', class_='list-group-item')
            for item in list_items:
                # Extract zone and price
                small_tag = item.find('small')
                if small_tag:
                    zone = clean_text(small_tag.get_text(strip=True).replace(':', ''))
                    price_p = item.find('p', class_='fs-16')
                    if price_p:
                        price_text = clean_text(price_p.get_text(strip=True))
                        price_match = re.search(r'(\d+)\s*جنيه/الدقيقة', price_text)
                        if price_match:
                            card_data[zone] = {
                                'price_per_minute': int(price_match.group(1)),
                                'currency': 'EGP'
                            }
    
    return card_data

def scrape_international_calls(html_content: str) -> Dict[str, Any]:
    """Main scraping function to extract all international calls data."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract page title and description
    title_section = soup.find('section', class_='page_title_test')
    title = ""
    description = ""
    
    if title_section:
        title_h1 = title_section.find('h1')
        if title_h1:
            title = clean_text(title_h1.get_text(strip=True))
        
        description_p = title_section.find('p', class_='fs-14')
        if description_p:
            description = clean_text(description_p.get_text(strip=True))
    
    # Extract pricing data
    pricing_data = extract_pricing_table(soup)
    
    # Extract card view data (as backup/alternative)
    card_data = extract_card_view_data(soup)
    
    # Merge pricing data
    if card_data:
        pricing_data.update(card_data)
    
    # Extract zone countries mapping
    zones_countries = extract_zone_countries(soup)
    
    # Extract satellite pricing
    satellite_pricing = extract_satellite_pricing(soup)
    
    # Extract Kol El Donia service
    kol_el_donia_service = extract_kol_el_donia_service(soup)
    
    # Extract other international services
    other_services = extract_other_international_services(soup)
    
    # Extract premium international numbers
    premium_numbers = extract_premium_international_numbers(soup)
    
    # Build final data structure
    final_data = {
        'page_url': 'https://www.eand.com.eg/StaticFiles/portal2/etisalat/pages/services/international_calls.html',
        'service_name': title or 'مكالمات دولية',
        'description': description,
        'pricing': pricing_data,
        'zones': zones_countries,
        'satellite_services': satellite_pricing,
        'kol_el_donia_service': kol_el_donia_service,
        'other_international_services': other_services,
        'premium_international_numbers': premium_numbers
    }
    
    return final_data

def save_to_json(data: Dict[str, Any], filename: str = 'International Calls/e&_international_calls.json'):
    """Save extracted data to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def main():
    """Main function to run the scraper."""    
    # Try to read from file first
    html_content = read_html_content('International Calls/page_content.txt')
    
    if html_content:
        # Extract data
        extracted_data = scrape_international_calls(html_content)
        # Save to JSON
        save_to_json(extracted_data)
            
    else:
        print("Failed to obtain HTML content")

if __name__ == "__main__":
    main()