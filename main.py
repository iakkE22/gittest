import os
import argparse
from xiaohongshu_crawler import XiaohongshuCrawler
from text_processor import PromotionalTextProcessor
from text_generator import PromotionalTextGenerator

def main():
    parser = argparse.ArgumentParser(description='Xiaohongshu Promotional Text Pipeline')
    parser.add_argument('--keywords', type=str, default='亲子家庭 旅游', 
                        help='Comma-separated keywords to search for')
    parser.add_argument('--posts_per_keyword', type=int, default=200, 
                        help='Number of posts to scrape per keyword')
    parser.add_argument('--headless', action='store_true', 
                        help='Run browser in headless mode')
    parser.add_argument('--output_dir', type=str, default='output', 
                        help='Directory to save output files')
    parser.add_argument('--processed_dir', type=str, default='processed_data', 
                        help='Directory to save processed data')
    parser.add_argument('--generated_dir', type=str, default='generated_text', 
                        help='Directory to save generated text')
    parser.add_argument('--skip_crawl', action='store_true', 
                        help='Skip crawling and use existing data')
    parser.add_argument('--skip_process', action='store_true', 
                        help='Skip processing and use existing processed data')
    parser.add_argument('--generate_only', type=str, default=None, 
                        help='Only generate text for this keyword (no crawling/processing)')
    parser.add_argument('--variations', type=int, default=3, 
                        help='Number of text variations to generate per keyword')
    
    args = parser.parse_args()
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',')]
    
    # Generate text only mode
    if args.generate_only:
        print(f"=== Generating promotional text for '{args.generate_only}' ===")
        generator = PromotionalTextGenerator(data_dir=args.processed_dir)
        generated_texts = generator.generate_promotional_text(args.generate_only, args.variations)
        
        if generated_texts:
            print("\nSample generated promotional text:\n")
            print(generated_texts[0])
            print("\n")
        
        generator.save_generated_text(args.generate_only, generated_texts, args.generated_dir)
        return
    
    # Crawling phase
    if not args.skip_crawl:
        print("=== Starting crawling phase ===")
        crawler = XiaohongshuCrawler(headless=args.headless, output_dir=args.output_dir)
        
        try:
            for keyword in keywords:
                print(f"\nCrawling for keyword: {keyword}")
                posts_data = crawler.search_by_keyword(keyword, args.posts_per_keyword)
                print(f"Successfully scraped {len(posts_data)} posts for '{keyword}'")
        finally:
            crawler.close()
    
    # Processing phase
    if not args.skip_process:
        print("\n=== Starting processing phase ===")
        processor = PromotionalTextProcessor(input_dir=args.output_dir, output_dir=args.processed_dir)
        all_patterns = processor.process_all_files()
        
        # Print stats
        print("\nExtracted patterns statistics:")
        print(f"- Point categories: {len(all_patterns['points'])}")
        print(f"- Section titles: {len(all_patterns['sections'])}")
        print(f"- Special offers: {len(all_patterns['special_offers'])}")
    
    # Generation phase
    print("\n=== Starting generation phase ===")
    generator = PromotionalTextGenerator(data_dir=args.processed_dir)
    
    for keyword in keywords:
        print(f"\nGenerating promotional text for '{keyword}'")
        generated_texts = generator.generate_promotional_text(keyword, args.variations)
        
        if generated_texts:
            print("\nSample generated promotional text:\n")
            print(generated_texts[0])
            print("\n")
        
        generator.save_generated_text(keyword, generated_texts, args.generated_dir)
    
    print("\n=== Pipeline completed successfully ===")

if __name__ == "__main__":
    main() 