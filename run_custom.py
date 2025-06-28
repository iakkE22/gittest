#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义数据清洗运行脚本
允许用户调整各种参数
"""

from data_cleaner import DataCleaner
import os

def run_custom_cleaning():
    """自定义参数运行数据清洗"""
    
    print("=== 小红书数据清洗工具 ===")
    print()
    
    # 参数配置
    print("请配置运行参数：")
    
    # 输入目录
    data_dir = input("数据目录 (默认: data): ").strip() or "data"
    if not os.path.exists(data_dir):
        print(f"错误：目录 {data_dir} 不存在")
        return
    
    # 输出目录
    output_dir = input("输出目录 (默认: cleaned_data): ").strip() or "cleaned_data"
    
    # 并发数
    max_workers_input = input("并发数 (1=串行，推荐；2-5=并行，需注意API限制，默认: 1): ").strip()
    try:
        max_workers = int(max_workers_input) if max_workers_input else 1
        if max_workers < 1:
            max_workers = 1
        elif max_workers > 5:
            print("警告：并发数过高可能导致API限制，已调整为5")
            max_workers = 5
    except ValueError:
        print("无效输入，使用默认值 1")
        max_workers = 1
    
    # 处理限制
    limit_input = input("处理条数限制 (0=不限制，默认: 0): ").strip()
    try:
        limit = int(limit_input) if limit_input else 0
    except ValueError:
        print("无效输入，使用默认值 0（不限制）")
        limit = 0
    
    print("\n=== 配置确认 ===")
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print(f"并发数: {max_workers} ({'串行处理' if max_workers == 1 else '并行处理'})")
    print(f"处理限制: {'无限制' if limit == 0 else f'{limit} 条'}")
    
    confirm = input("\n确认开始处理？(y/N): ").strip().lower()
    if confirm != 'y':
        print("取消处理")
        return
    
    # 开始处理
    print("\n开始数据清洗...")
    
    cleaner = DataCleaner()
    
    # 如果有限制，需要修改cleaner
    if limit > 0:
        print(f"注意：将限制处理前 {limit} 条数据")
    
    try:
        results = cleaner.clean_all_data(
            data_dir=data_dir,
            output_dir=output_dir,
            max_workers=max_workers
        )
        
        print("\n=== 处理完成 ===")
        total = sum(len(data) for data in results.values())
        print(f"总共处理: {total} 条文案")
        
        for category, data in results.items():
            print(f"  {category}: {len(data)} 条")
        
        print(f"\n结果保存在: {output_dir}")
        
    except KeyboardInterrupt:
        print("\n\n用户中断处理")
    except Exception as e:
        print(f"\n处理出错: {str(e)}")

def run_batch_test():
    """批量测试模式"""
    print("=== 批量测试模式 ===")
    
    # 查找所有JSON文件
    import glob
    json_files = glob.glob("data/**/*.json", recursive=True)
    
    if not json_files:
        print("未找到JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个文件:")
    for i, file in enumerate(json_files, 1):
        print(f"  {i}. {file}")
    
    # 选择文件
    choice = input(f"\n选择要测试的文件 (1-{len(json_files)}, 0=全部): ").strip()
    
    if choice == "0":
        test_files = json_files
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(json_files):
                test_files = [json_files[idx]]
            else:
                print("无效选择")
                return
        except ValueError:
            print("无效输入")
            return
    
    # 设置测试数量
    test_count = input("每个文件测试多少条数据 (默认: 3): ").strip()
    try:
        test_count = int(test_count) if test_count else 3
    except ValueError:
        test_count = 3
    
    print(f"\n将测试 {len(test_files)} 个文件，每个文件前 {test_count} 条数据")
    
    # 开始测试
    cleaner = DataCleaner()
    
    for file_path in test_files:
        print(f"\n{'='*50}")
        print(f"测试文件: {file_path}")
        
        try:
            # 读取文件
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_data = data[:test_count]
            print(f"测试 {len(test_data)} 条数据")
            
            results = []
            for i, item in enumerate(test_data):
                print(f"\n--- 第 {i+1} 条 ---")
                result = cleaner.process_single_text(item)
                if result:
                    results.append(result)
                    print("✓ 处理成功")
                else:
                    print("✗ 处理失败或被过滤")
            
            print(f"\n文件 {file_path} 测试完成")
            print(f"成功处理: {len(results)}/{len(test_data)} 条")
            
        except Exception as e:
            print(f"测试文件 {file_path} 时出错: {str(e)}")

def main():
    """主菜单"""
    while True:
        print("\n" + "="*50)
        print("小红书数据清洗工具")
        print("="*50)
        print("1. 自定义参数运行完整清洗")
        print("2. 批量测试模式")
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == "1":
            run_custom_cleaning()
        elif choice == "2":
            run_batch_test()
        elif choice == "3":
            print("再见！")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main() 