"""Simple live test to extract a specific icon image URL."""

import os
import requests
from bs4 import BeautifulSoup

def test_manual_icon_extraction():
    """Manually test extracting a specific icon from yotoicons.com."""
    
    # Test connecting to a specific category page
    test_urls = [
        "https://yotoicons.com/icons?tag=food",
        "https://yotoicons.com/icons?tag=animals",
        "https://yotoicons.com/icons?tag=weather"
    ]
    
    for test_url in test_urls:
        print(f"\n🔍 Testing: {test_url}")
        try:
            response = requests.get(test_url, timeout=30)
            if response.status_code == 200:
                print(f"   ✅ Connected successfully")
                
                # Parse the page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for images or SVGs
                images = soup.find_all('img')
                svgs = soup.find_all('svg')
                
                print(f"   📊 Found {len(images)} images and {len(svgs)} SVG elements")
                
                # Look for any links to individual icon pages
                links = soup.find_all('a', href=True)
                icon_page_links = []
                for link in links:
                    href = link.get('href')
                    if href and ('icon' in href.lower() or href.startswith('/icons/')):
                        icon_page_links.append(href)
                
                if icon_page_links:
                    print(f"   🎯 Found {len(icon_page_links)} potential icon page links:")
                    for link in icon_page_links[:3]:  # Show first 3
                        print(f"      - {link}")
                
                # Look for direct image URLs
                image_urls = []
                for img in images[:5]:  # Check first 5 images
                    src = img.get('src')
                    if src and any(ext in src for ext in ['.svg', '.png', '.jpg']):
                        if src.startswith('/'):
                            src = f"https://yotoicons.com{src}"
                        elif src.startswith('//'):
                            src = f"https:{src}"
                        image_urls.append(src)
                
                if image_urls:
                    print(f"   🖼️  Found {len(image_urls)} direct image URLs:")
                    for img_url in image_urls[:3]:  # Show first 3
                        print(f"      - {img_url}")
                        
                        # Test if the image URL is accessible
                        try:
                            img_response = requests.get(img_url, timeout=10)
                            if img_response.status_code == 200:
                                content_type = img_response.headers.get('content-type', '')
                                print(f"        ✅ Accessible ({content_type}, {len(img_response.content)} bytes)")
                            else:
                                print(f"        ❌ Not accessible ({img_response.status_code})")
                        except Exception as e:
                            print(f"        ⚠️  Could not test accessibility: {e}")
                
                break  # Success, no need to try other URLs
                
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_manual_icon_extraction()
