"""Command-line interface for icon curator."""

import argparse
import logging
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
        service = IconService()
        
        print("Starting icon scraping from yotoicons.com...")
        result = service.scrape_and_store_icons(force_update=args.force_update)
        
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
            print(f"Image: {icon.image_url}")
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
        '--force-update',
        action='store_true',
        help='Update existing icons'
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
