"""CLI entry point for Market Radar - HeadHunter vacancies fetcher."""

import argparse
import logging
import sys

from .hh_client import fetch_all_vacancies, save_to_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="market_radar_cli",
        description="Fetch vacancies from HeadHunter API and save to CSV"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        default="python backend OR python developer",
        help="Search query text (default: 'python backend OR python developer')"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=30,
        help="Number of vacancies to fetch (default: 30)"
    )
    
    parser.add_argument(
        "--area", "-a",
        type=int,
        default=113,
        help="Area ID (default: 113 - Russia)"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    if args.limit < 1:
        logger.error("Limit must be at least 1")
        return 1
    
    if args.limit > 1000:
        logger.warning("Limit > 1000 may take a long time due to API rate limits")
    
    try:
        vacancies = fetch_all_vacancies(
            query=args.query,
            area=args.area,
            limit=args.limit
        )
        
        if not vacancies:
            logger.warning("No vacancies found")
            return 0
        
        filename = save_to_csv(vacancies, args.query)
        print(f"\n✓ Saved {len(vacancies)} vacancies to: {filename}")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
