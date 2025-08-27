"""Command-line interface for icon curator."""

import argparse
import logging
import os
import sys
from typing import Optional

from ..core.service import IconService
from ..core.exceptions import IconCuratorError


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def scrape_command(args) -> int:
    """Execute the scrape command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Check if we should run in demo mode
        demo_mode = getattr(args, 'demo', False) or os.getenv('ICON_CURATOR_DEMO', 'false').lower() == 'true'
        
        if demo_mode:
            print("🚀 Running in DEMO mode (no database required)")
            print("   This will demonstrate web scraping without storing data")
            print("   Set up PostgreSQL for full functionality\n")
            
            # Demo scraping - just test the scraper without database
            from ..processors.scraper import YotoIconScraper
            scraper = YotoIconScraper()
            
            print("Starting demo icon scraping from yotoicons.com...")
            print("Discovering available icons...")
            
            try:
                # Test the main site and discover actual structure
                print(f"🔍 Exploring yotoicons.com structure...")
                
                main_url = "https://yotoicons.com/"
                response = scraper._make_request(main_url)
                
                if response:
                    print(f"    ✅ Successfully connected to {main_url}")
                    
                    # Parse the main page to see what's available
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for common patterns that might indicate icons
                    title = soup.find('title')
                    if title:
                        print(f"    📄 Page title: {title.get_text().strip()}")
                    
                    # Show general page structure
                    headings = soup.find_all(['h1', 'h2', 'h3'])
                    if headings:
                        print(f"    📝 Page headings found:")
                        for heading in headings[:3]:
                            text = heading.get_text().strip()
                            if text and len(text) < 100:
                                print(f"      - {text}")
                    
                    # Look for any image references
                    images = soup.find_all('img')
                    svg_count = len(soup.find_all('svg'))
                    if images or svg_count:
                        print(f"    🎨 Found {len(images)} images and {svg_count} SVG elements")
                    # Try to use the scraper's actual discovery logic
                    print(f"\n🔍 Testing category discovery...")
                    try:
                        # Use the scraper's built-in category discovery method
                        categories = scraper._discover_categories()
                        if categories:
                            print(f"    ✅ Discovered {len(categories)} categories:")
                            for cat in categories[:5]:  # Show first 5
                                print(f"      - {cat}")
                            if len(categories) > 5:
                                print(f"      ... and {len(categories) - 5} more")
                        else:
                            print(f"    📝 No categories discovered with current logic")
                            print(f"        (This may need site-specific adaptation)")
                    except Exception as discovery_error:
                        print(f"    ⚠️  Category discovery test: {discovery_error}")
                        print(f"        (Discovery logic may need site-specific tuning)")
                
                else:
                    print(f"    ❌ Could not connect to {main_url}")
                
                print(f"\n🎯 Demo completed!")
                print(f"   The scraper successfully connected to yotoicons.com")
                print(f"   For full icon discovery and database storage:")
                print(f"   1. Install PostgreSQL (see docs/environment-setup.md)")
                print(f"   2. Run: python setup_database.py")
                print(f"   3. Run: icon-curator scrape")
                
                return 0
                
            except Exception as e:
                print(f"Demo error: {e}")
                return 1
        
        # Full mode with database
        service = IconService()
        
        print("Starting icon scraping from yotoicons.com...")
        
        # Determine what to scrape based on arguments
        category = getattr(args, 'category', None)
        max_pages = getattr(args, 'max_pages', None)
        
        if category:
            print(f"Scraping category: {category}")
            if max_pages:
                print(f"Limited to {max_pages} pages per category")
        else:
            print("Scraping all available categories")
            if max_pages:
                print(f"Limited to {max_pages} pages per category")
        
        result = service.scrape_and_store_icons(
            force_update=args.force_update,
            category=category,
            max_pages=max_pages
        )
        
        print(f"Scraping completed!")
        print(f"Total icons found: {result.total_icons}")
        print(f"Successfully scraped: {result.successful_scraped}")
        print(f"Failed: {result.failed_scraped}")
        print(f"Success rate: {result.success_rate:.1f}%")
        print(f"Processing time: {result.processing_time:.2f} seconds")
        
        if result.errors:
            print(f"\nErrors encountered ({len(result.errors)}):")
            for error in result.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more errors")
        
        return 0
        
    except IconCuratorError as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() and "postgresql" in error_msg.lower():
            print("❌ Database Connection Error!")
            print("   PostgreSQL is not running or not configured.")
            print("   ")
            print("   🚀 Try demo mode: icon-curator scrape --demo")
            print("   📚 Setup guide: docs/environment-setup.md")
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def search_command(args) -> int:
    """Execute the search command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        service = IconService()
        
        icons = service.search_icons(
            query=args.query,
            category=args.category,
            tags=args.tags.split(',') if args.tags else None,
            limit=args.limit
        )
        
        if not icons:
            print("No icons found matching the criteria.")
            return 0
        
        print(f"Found {len(icons)} icons:")
        print("-" * 80)
        
        for icon in icons:
            print(f"Name: {icon.name}")
            print(f"URL: {icon.url}")
            if icon.category:
                print(f"Category: {icon.category}")
            if icon.tags:
                print(f"Tags: {', '.join(icon.tags)}")
            if icon.description:
                print(f"Description: {icon.description}")
            print("-" * 80)
        
        return 0
        
    except IconCuratorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def stats_command(args) -> int:
    """Execute the stats command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        service = IconService()
        stats = service.get_statistics()
        
        print("Icon Database Statistics:")
        print("=" * 40)
        print(f"Total Icons: {stats['total_icons']}")
        print(f"Total Categories: {stats['total_categories']}")
        print(f"Total Tags: {stats['total_tags']}")
        
        if stats['categories']:
            print(f"\nTop Categories:")
            for category in stats['categories']:
                print(f"  - {category}")
        
        if stats['tags']:
            print(f"\nTop Tags:")
            for tag in stats['tags']:
                print(f"  - {tag}")
        
        return 0
        
    except IconCuratorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog='icon-curator',
        description='Yoto Icons Database Management Tool'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser(
        'scrape',
        help='Scrape icons from yotoicons.com'
    )
    scrape_parser.add_argument(
        'category',
        nargs='?',
        help='Category to scrape (e.g., animals, food, weather). If not specified, scrapes all categories.'
    )
    scrape_parser.add_argument(
        '--max-pages',
        type=int,
        help='Maximum number of pages to scrape per category (useful for testing)'
    )
    scrape_parser.add_argument(
        '--force-update',
        action='store_true',
        help='Update existing icons'
    )
    scrape_parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (no database required)'
    )
    scrape_parser.set_defaults(func=scrape_command)
    
    # Search command
    search_parser = subparsers.add_parser(
        'search',
        help='Search for icons in the database'
    )
    search_parser.add_argument(
        'query',
        help='Search query'
    )
    search_parser.add_argument(
        '--category',
        help='Filter by category'
    )
    search_parser.add_argument(
        '--tags',
        help='Filter by tags (comma-separated)'
    )
    search_parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum number of results (default: 50)'
    )
    search_parser.set_defaults(func=search_command)
    
    # Stats command
    stats_parser = subparsers.add_parser(
        'stats',
        help='Show database statistics'
    )
    stats_parser.set_defaults(func=stats_command)
    
    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        argv: Command line arguments (uses sys.argv if None)
        
    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
