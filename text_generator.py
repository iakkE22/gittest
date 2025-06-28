import os
import json
import random
import argparse
from collections import defaultdict

class PromotionalTextGenerator:
    def __init__(self, data_dir="processed_data"):
        self.data_dir = data_dir
        self.patterns = self._load_patterns()
        
    def _load_patterns(self):
        """Load processed pattern data"""
        all_patterns_path = os.path.join(self.data_dir, 'all_promotional_patterns.json')
        
        if not os.path.exists(all_patterns_path):
            print(f"Error: Data file not found at {all_patterns_path}")
            return {
                "points": defaultdict(list),
                "sections": defaultdict(list),
                "special_offers": []
            }
            
        with open(all_patterns_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_promotional_text(self, product_keyword, num_variations=3):
        """Generate promotional text for a product based on keyword"""
        results = []
        
        for _ in range(num_variations):
            # Create a promotional text structure
            promo_text = self._generate_single_variation(product_keyword)
            results.append(promo_text)
            
        return results
    
    def _generate_single_variation(self, product_keyword):
        """Generate a single variation of promotional text"""
        # Choose a random section title or create one with the product keyword
        if self.patterns["sections"] and random.random() > 0.3:
            section_title = random.choice(list(self.patterns["sections"].keys()))
        else:
            section_title = f"{product_keyword}必选" if random.random() > 0.5 else f"{product_keyword}推荐"
        
        # Create the main title
        main_title = f"【{section_title}】 {self._generate_catchy_subtitle(product_keyword)}"
        
        # Generate pain points (痛点)
        pain_points = []
        if "痛点" in self.patterns["points"] and self.patterns["points"]["痛点"]:
            pain_point = random.choice(self.patterns["points"]["痛点"])["content"]
            pain_points.append(f"- 痛点：{pain_point}")
        else:
            pain_points.append(f"- 痛点：想体验{product_keyword}但担心质量不佳?")
        
        # Generate solutions (方案)
        solutions = []
        if "方案" in self.patterns["points"] and self.patterns["points"]["方案"]:
            solution = random.choice(self.patterns["points"]["方案"])["content"]
            solutions.append(f"- 方案：{solution}")
        else:
            solutions.append(f"- 方案：专业{product_keyword}体验，高品质保证!")
        
        # Generate pricing (价格)
        pricing = []
        if "价格" in self.patterns["points"] and self.patterns["points"]["价格"]:
            price = random.choice(self.patterns["points"]["价格"])["content"]
            pricing.append(f"- 价格：{price}")
        else:
            price = f"¥{random.randint(199, 999)}/人"
            pricing.append(f"- 价格：{price}，超值体验!")
        
        # Generate special offer
        special_offers = []
        if self.patterns["special_offers"]:
            offer = random.choice(self.patterns["special_offers"])["content"]
            special_offers.append(f"✨{offer}")
        else:
            special_offers.append(f"✨私戳享受{product_keyword}折扣福利!")
        
        # Combine all elements
        promotional_text = [
            main_title,
            "",
            *pain_points,
            "",
            *solutions,
            "",
            *pricing,
            "",
            *special_offers
        ]
        
        return "\n".join(promotional_text)
    
    def _generate_catchy_subtitle(self, keyword):
        """Generate a catchy subtitle based on keyword"""
        templates = [
            f"{keyword}体验+专业服务!",
            f"高品质{keyword}，值得体验!",
            f"独家{keyword}，限时特惠!",
            f"超值{keyword}，口碑推荐!",
            f"{keyword}专享，不容错过!"
        ]
        return random.choice(templates)
    
    def save_generated_text(self, product_keyword, generated_texts, output_dir="generated_text"):
        """Save generated promotional texts to file"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, f"{product_keyword}_promo_text.txt")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, text in enumerate(generated_texts, 1):
                f.write(f"===== 变体 {i} =====\n\n")
                f.write(text)
                f.write("\n\n")
                
        print(f"Generated promotional texts saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate promotional text for products')
    parser.add_argument('--keyword', type=str, required=True, 
                        help='Product keyword to generate promotional text for')
    parser.add_argument('--variations', type=int, default=3, 
                        help='Number of text variations to generate')
    parser.add_argument('--data_dir', type=str, default='processed_data', 
                        help='Directory containing processed pattern data')
    parser.add_argument('--output_dir', type=str, default='generated_text', 
                        help='Directory to save generated text')
    
    args = parser.parse_args()
    
    generator = PromotionalTextGenerator(data_dir=args.data_dir)
    generated_texts = generator.generate_promotional_text(args.keyword, args.variations)
    
    # Print first generated text
    if generated_texts:
        print("\nSample generated promotional text:\n")
        print(generated_texts[0])
        print("\n")
    
    generator.save_generated_text(args.keyword, generated_texts, args.output_dir) 