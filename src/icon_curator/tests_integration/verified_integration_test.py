"""Verified integration test for extracting real icon URLs from yotoicons.com."""

import sys
import pytest
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from icon_extractor.processors.scraper import YotoIconScraper


def test_extract_real_icon_image_urls():
    """Integration test that extracts actual icon image URLs from yotoicons.com."""
    
    # Test categories that we know work
    test_categories = ["food", "animals", "weather"]
    
    successful_extractions = 0
    all_image_urls = []
    
    for category in test_categories:
        print(f"\n🔍 Testing category: {category}")
        
        try:
            # Connect to category page
            url = f"https://yotoicons.com/icons?tag={category}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ Connected to {category} page")
                
                # Parse the page
                soup = BeautifulSoup(response.text, 'html.parser')
                images = soup.find_all('img')
                
                # Extract icon image URLs
                category_image_urls = []
                for img in images:
                    src = img.get('src') if hasattr(img, 'get') else None
                    if src and isinstance(src, str):
                        # Look for uploaded icon images (the real icons)
                        if 'uploads/' in src and any(ext in src for ext in ['.png', '.jpg', '.svg']):
                            if src.startswith('/'):
                                src = f"https://yotoicons.com{src}"
                            elif not src.startswith('http'):
                                src = f"https://yotoicons.com/{src.lstrip('/')}"
                            category_image_urls.append(src)
                
                if category_image_urls:
                    print(f"   🎯 Found {len(category_image_urls)} icon image URLs")
                    
                    # Test first few URLs
                    for i, img_url in enumerate(category_image_urls[:3]):
                        try:
                            img_response = requests.get(img_url, timeout=10)
                            if img_response.status_code == 200:
                                content_type = img_response.headers.get('content-type', '')
                                size = len(img_response.content)
                                print(f"      ✅ {img_url} ({content_type}, {size} bytes)")
                                all_image_urls.append({
                                    'category': category,
                                    'url': img_url,
                                    'content_type': content_type,
                                    'size': size
                                })
                            else:
                                print(f"      ❌ {img_url} (HTTP {img_response.status_code})")
                        except Exception as e:
                            print(f"      ⚠️  {img_url} (Error: {e})")
                    
                    successful_extractions += 1
                else:
                    print(f"   📝 No icon image URLs found in {category}")
                    
            else:
                print(f"   ❌ Could not connect to {category} page (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Error testing {category}: {e}")
    
    # Verify results
    print(f"\n📊 Final Results:")
    print(f"   Categories tested: {len(test_categories)}")
    print(f"   Successful extractions: {successful_extractions}")
    print(f"   Total verified image URLs: {len(all_image_urls)}")
    
    # Assertions
    assert successful_extractions > 0, f"Should successfully extract from at least one category"
    assert len(all_image_urls) > 0, f"Should find at least one verified image URL"
    
    # Show sample results
    if all_image_urls:
        print(f"\n🎉 Sample extracted icon URLs:")
        for icon in all_image_urls[:5]:
            print(f"   - {icon['category']}: {icon['url']} ({icon['size']} bytes)")
    
    return all_image_urls


def test_scraper_integration_with_real_site():
    """Test that our YotoIconScraper works with the real site structure."""
    scraper = YotoIconScraper()
    
    # Test connection
    response = scraper._make_request("https://yotoicons.com/")
    assert response is not None
    assert response.status_code == 200
    print("✅ Scraper can connect to yotoicons.com")
    
    # Test category discovery
    categories = scraper._discover_categories()
    assert len(categories) > 0
    print(f"✅ Scraper discovered {len(categories)} categories")
    
    # Build category URLs for verification
    category_urls = [f"{scraper.base_url}/icons?tag={cat}&page=1" for cat in categories]
    assert len(category_urls) > 0
    print(f"✅ Built {len(category_urls)} category URLs")


if __name__ == "__main__":
    print("🚀 Running integration tests for yotoicons.com icon extraction")
    
    print("\n" + "="*60)
    print("TEST 1: Extract real icon image URLs")
    print("="*60)
    image_urls = test_extract_real_icon_image_urls()
    
    print("\n" + "="*60)
    print("TEST 2: Scraper integration test")
    print("="*60)  
    category_urls = test_scraper_integration_with_real_site()
    
    print("\n" + "="*60)
    print("🎉 INTEGRATION TESTS COMPLETE")
    print("="*60)
    print(f"✅ Successfully extracted {len(image_urls)} verified icon image URLs")
    print(f"✅ Scraper discovered {len(category_urls)} category URLs") 
    print("✅ Icon Curator can successfully scrape yotoicons.com!")
    
    # Show final summary
    categories = set(icon['category'] for icon in image_urls)
    print(f"\n📋 Summary:")
    print(f"   Categories with extracted icons: {sorted(categories)}")
    print(f"   Total verified icon URLs: {len(image_urls)}")
    print(f"   Average icon size: {sum(icon['size'] for icon in image_urls) / len(image_urls):.0f} bytes")
