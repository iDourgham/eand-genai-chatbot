import json
from bs4 import BeautifulSoup
import re

def extract_etisalat_data(html_content):
    """Extract information from Etisalat HTML page using Beautiful Soup"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    extracted_data = {
        "page_url": "https://www.eand.com.eg/StaticFiles/portal2/etisalat/pages/services/out_of_credit.html",
        "service_name": "",
        "service_description": "",
        "service_features": [],
        "service_costs": [],
        "usage_instructions": ""
    }
    
    # Extract service name
    title_element = soup.find('h1', class_='GESSTwoBold_font')
    if title_element:
        extracted_data["service_name"] = title_element.get_text(strip=True)
    
    # Extract service description
    description_elements = soup.find_all('p', class_='fs-14 grey-color')
    service_description = " ".join([desc.get_text(strip=True) for desc in description_elements if desc.get_text(strip=True)])
    extracted_data["service_description"] = service_description
    
    # Extract usage instructions
    usage_element = soup.find('h5', class_='mt-4 header-service')
    if usage_element:
        extracted_data["usage_instructions"] = usage_element.get_text(strip=True)
    
    # Extract service features
    features_section = soup.find('section', id='for_features_and_terms')
    if features_section:
        feature_paragraphs = features_section.find_all('p')
        for p in feature_paragraphs:
            text = p.get_text(strip=True)
            if re.match(r'^\d+\s*⚊', text):
                # Remove newline characters from the feature text
                clean_text = text.replace('\n', ' ').replace('\r', ' ')
                # Also remove multiple spaces that might result from newline removal
                clean_text = re.sub(r'\s+', ' ', clean_text)
                extracted_data["service_features"].append(clean_text)
    
    # Extract service costs
    costs_section = soup.find('section', id='for_points')
    if costs_section:
        cost_cards = costs_section.find_all('div', class_='card')
        for card in cost_cards:
            title_element = card.find('h2', class_='card-title')
            body_element = card.find('div', class_='card-body')
            
            if title_element and body_element:
                cost_info = {
                    "service_fee": title_element.get_text(strip=True),
                    "loan_amount": body_element.get_text(strip=True)
                }
                extracted_data["service_costs"].append(cost_info)
    
    return extracted_data

def save_to_json(data, filename='e&_super_salefny.json'):
    """Save extracted data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {filename}")

def read_html_file(filename='page_content.txt'):
    """Read HTML content from text file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return None

def main():
    html_content = read_html_file()
    if html_content is None:
        return
    
    extracted_data = extract_etisalat_data(html_content)
    save_to_json(extracted_data)
    
    print("Extracted Data:")
    print("=" * 50)
    print(json.dumps(extracted_data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()