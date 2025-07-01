import json
from bs4 import BeautifulSoup
import re

def scrape_prepaid_data_packages():
    """
    Scrape prepaid data packages information from HTML file and save to JSON
    """
    
    # Read HTML content from file
    try:
        with open('Pre-Paid Data Packages/page_content.txt', 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print("Error: page_content.txt file not found!")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize data structure
    scraped_data = {
        "page_info": {
            "url": "https://www.eand.com.eg/StaticFiles/portal2/etisalat/pages/super_connect_home/prepaid_bundles.html",
            "title": "باقات الداتا المدفوعة مقدما",
            "description": "النت مكمل كده كده مع باقات الداتا المدفوعة مقدما بصلاحية شهر، ثلاث شهور أو ستة أشهر"
        },
        "main_packages": [],
        "additional_packages": [],
        "package_features": []
    }
    
    # Extract main data packages from table
    def extract_main_packages():
        packages = []
        
        # Find all package cards in the slider
        package_cards = soup.find_all('div', class_='card border-radius-RTB')
        
        for card in package_cards:
            package = {}
            
            # Extract package name
            name_elem = card.find('h5', class_='plan-name blue-color')
            if name_elem:
                package['name'] = name_elem.get_text(strip=True)
            
            # Extract price
            price_elem = card.find('h5', class_='plan-price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract number from price
                price_match = re.search(r'(\d+)', price_text)
                if price_match:
                    package['price'] = int(price_match.group(1))
                    package['currency'] = 'جنية'
            
            # Extract validity period
            validity_elem = card.find('span', class_='plan-hint mediumGrey-color')
            if validity_elem:
                package['validity'] = validity_elem.get_text(strip=True)
            
            # Extract data amount
            data_elem = card.find('p', class_='ff-suissintl-bold fs-16')
            if data_elem:
                package['data_amount'] = data_elem.get_text(strip=True)
            
            # Extract offer description
            offer_elem = card.find('p', class_='fs-11')
            if offer_elem:
                package['offer_description'] = offer_elem.get_text(strip=True)
            
            if package:  # Only add if we found some data
                packages.append(package)
        
        # Also extract from table format if cards are empty
        if not packages:
            table_rows = soup.find_all('tr')
            for row in table_rows:
                cells = row.find_all('td')
                for cell in cells:
                    package = {}
                    
                    name_elem = cell.find('h5', class_='plan-name blue-color')
                    price_elem = cell.find('h5', class_='plan-price')
                    validity_elem = cell.find('p', class_='plan-hint mediumGrey-color')
                    
                    if name_elem and price_elem:
                        package['name'] = name_elem.get_text(strip=True)
                        
                        price_text = price_elem.get_text(strip=True)
                        price_match = re.search(r'(\d+)', price_text)
                        if price_match:
                            package['price'] = int(price_match.group(1))
                            package['currency'] = 'جنية'
                        
                        if validity_elem:
                            package['validity'] = validity_elem.get_text(strip=True)
                        
                        packages.append(package)
        
        return packages
    
    # Extract additional packages (Extra packages)
    def extract_additional_packages():
        additional_packages = []
        
        # Find the section with additional packages
        additional_section = soup.find('section', id='for_textContainer')
        if additional_section:
            package_containers = additional_section.find_all('div', class_='text-container border-top-right-radius p-3')
            
            for container in package_containers:
                package = {}
                
                # Extract package name
                name_elem = container.find('h5', class_='yellow-color extra-name')
                if name_elem:
                    package['name'] = name_elem.get_text(strip=True)
                
                # Extract price
                price_elem = container.find('h6', class_='extra-price')
                if not price_elem:
                    price_elem = container.find('h6', class_='mt-3 extra-price')
                
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'(\d+)', price_text)
                    if price_match:
                        package['price'] = int(price_match.group(1))
                        package['currency'] = 'جنية'
                
                # Extract validity
                validity_elem = container.find('p', class_='mt-2 extra-hint')
                if validity_elem:
                    package['validity'] = validity_elem.get_text(strip=True)
                
                # Extract data amount
                data_elem = container.find('h6', class_='extra-subPlanName mb-1')
                if data_elem:
                    package['data_amount'] = data_elem.get_text(strip=True)
                
                # Extract activation code
                activation_elem = container.find('b', class_='red-color')
                if activation_elem:
                    package['activation_code'] = activation_elem.get_text(strip=True)
                
                if package:
                    additional_packages.append(package)
        
        return additional_packages
    
    # Extract package features and terms
    def extract_package_features():
        features = []
        
        # Find the features section
        features_section = soup.find('section', id='for_features_and_terms')
        if features_section:
            feature_items = features_section.find_all('div', class_='col-sm-12 col-md-6 col-lg-4 my-3 d-flex')
            
            for item in feature_items:
                feature = {}
                
                # Extract feature number
                number_elem = item.find('span')
                if number_elem:
                    feature['number'] = number_elem.get_text(strip=True)
                
                # Extract feature description
                desc_elem = item.find('p', class_='fs-16')
                if desc_elem:
                    feature['description'] = desc_elem.get_text(strip=True)
                
                features.append(feature)
        
        return features
    
    # Scrape all sections
    scraped_data['main_packages'] = extract_main_packages()
    scraped_data['additional_packages'] = extract_additional_packages()
    scraped_data['package_features'] = extract_package_features()
    
    # Save to JSON file
    try:
        with open('Pre-Paid Data Packages/e&_prepaid_data_packages.json', 'w', encoding='utf-8') as json_file:
            json.dump(scraped_data, json_file, ensure_ascii=False, indent=2)
        
        print("✅ Data successfully scraped and saved to 'e&_prepaid_data_packages.json'")
        print(f"📊 Found {len(scraped_data['main_packages'])} main packages")
        print(f"📊 Found {len(scraped_data['additional_packages'])} additional packages")
        print(f"📊 Found {len(scraped_data['package_features'])} package features")
        
    except Exception as e:
        print(f"Error saving JSON file: {e}")
    
    return scraped_data


if __name__ == "__main__":
    print("🚀 Starting E& Prepaid Data Packages Scraper...")
    # Run the scraper
    scraped_data = scrape_prepaid_data_packages()
    print("\n✨ Scraping completed!")