import os
import json
import argparse
from collections import defaultdict

class PromotionalTextProcessor:
    def __init__(self, input_dir="output", output_dir="processed_data"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def process_all_files(self):
        """Process all JSON files in the input directory"""
        all_patterns = {
            "points": defaultdict(list),
            "sections": defaultdict(list),
            "special_offers": []
        }
        
        # Get all JSON files
        json_files = [f for f in os.listdir(self.input_dir) if f.endswith('.json')]
        
        for file in json_files:
            file_path = os.path.join(self.input_dir, file)
            keyword = file.replace('_posts.json', '')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            
            # Process each post
            for post in posts_data:
                if 'promotional_text' in post and post['promotional_text']:
                    self._process_post_patterns(post['promotional_text'], keyword, all_patterns)
        
        # Save processed data
        self._save_processed_data(all_patterns)
        return all_patterns
    
    def _process_post_patterns(self, promotional_text, keyword, all_patterns):
        """Process promotional text patterns from a post"""
        for pattern in promotional_text:
            pattern_type = pattern.get('type')
            
            if pattern_type == 'point':
                category = pattern.get('category')
                content = pattern.get('content')
                all_patterns['points'][category].append({
                    'content': content,
                    'keyword': keyword
                })
                
            elif pattern_type == 'section':
                title = pattern.get('title')
                content = pattern.get('content')
                all_patterns['sections'][title].append({
                    'content': content,
                    'keyword': keyword
                })
                
            elif pattern_type == 'special_offer':
                content = pattern.get('content')
                all_patterns['special_offers'].append({
                    'content': content,
                    'keyword': keyword
                })
    
    def _save_processed_data(self, all_patterns):
        """Save processed data to JSON files"""
        # Save points by category
        points_path = os.path.join(self.output_dir, 'points_by_category.json')
        with open(points_path, 'w', encoding='utf-8') as f:
            json.dump(all_patterns['points'], f, ensure_ascii=False, indent=2)
        
        # Save sections by title
        sections_path = os.path.join(self.output_dir, 'sections_by_title.json')
        with open(sections_path, 'w', encoding='utf-8') as f:
            json.dump(all_patterns['sections'], f, ensure_ascii=False, indent=2)
        
        # Save special offers
        offers_path = os.path.join(self.output_dir, 'special_offers.json')
        with open(offers_path, 'w', encoding='utf-8') as f:
            json.dump(all_patterns['special_offers'], f, ensure_ascii=False, indent=2)
        
        # Save all data combined
        all_path = os.path.join(self.output_dir, 'all_promotional_patterns.json')
        with open(all_path, 'w', encoding='utf-8') as f:
            json.dump(all_patterns, f, ensure_ascii=False, indent=2)
        
        print(f"Processed data saved to {self.output_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Xiaohongshu promotional text')
    parser.add_argument('--input_dir', type=str, default='output', 
                        help='Directory containing crawler output files')
    parser.add_argument('--output_dir', type=str, default='processed_data', 
                        help='Directory to save processed data')
    
    args = parser.parse_args()
    
    processor = PromotionalTextProcessor(input_dir=args.input_dir, output_dir=args.output_dir)
    processor.process_all_files() 