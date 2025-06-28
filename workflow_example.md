# 自动填补脚本工作流程示例

## 步骤详解

### 1. 读取JSON文件
```python
# 读取 cleaned_data/cultural_cleaned.json
data = json.load(f)
# 找到某个项目，比如：
{
    "id": "debug_post_105.txt",
    "original_text": "穿越时空的奇旅《吉祥如意》沉浸式体验...",
    "适用人群": "",           # ← 空缺
    "写作风格": "默认",        # ← 需要改进
    "商户": "",              # ← 空缺
    "商品名称": "",           # ← 空缺
    "景点名称": [],          # ← 空缺
    "地点信息": [],          # ← 空缺
    "服务内容": [],          # ← 空缺
    "其他关键词": []         # ← 空缺
}
```

### 2. 检查空缺字段
```python
empty_fields = []
if not current_data.get("适用人群") or current_data.get("适用人群") == "":
    empty_fields.append("适用人群")
if current_data.get("写作风格") == "默认":
    empty_fields.append("写作风格")
# ... 检查其他字段
# 结果：empty_fields = ["适用人群", "写作风格", "商户", "商品名称", "景点名称", "地点信息", "服务内容", "其他关键词"]
```

### 3. 读取对应的原始文件
```python
# 根据 id "debug_post_105.txt" 读取原始文件
original_file_path = "data/cultural/debug_post_105.txt"
original_content = read_original_file(original_file_path)
# 得到完整的原始文案内容：
"""
穿越时空的奇旅《吉祥如意》沉浸式体验
这个春节，去哪玩？在千年杨柳青古镇经历了一场如梦似幻的文化穿越。
作为《吉祥如意》沉浸式戏剧的首批体验者，这场以"年画失窃案"为引的古镇奇遇...
踏入民俗文化馆的瞬间，时空仿佛被重新编织...
@调皮蓝垫纸（卷土重来版） #调皮蓝垫纸观演团 @《吉祥如意》沉浸式互动戏剧 
#吉祥如意沉浸式互动戏剧#西青本地人去哪儿玩儿#天津年轻人聚集地#杨柳青民俗文化馆
"""
```

### 4. AI分析并填补
```python
# 构建提示词，包含：
# - 原始文案内容
# - 当前已有数据
# - 需要填补的字段列表
prompt = f"""
请根据以下小红书旅游文案内容，填补缺失的字段信息：

原始文案内容：
{original_content}

需要填补的字段：{empty_fields}
...
"""

# AI分析后返回：
{
    "id": "debug_post_105.txt",
    "适用人群": "年轻群体",      # ← 从"天津年轻人聚集地"标签分析得出
    "写作风格": "通俗易懂",      # ← 从文案风格分析得出
    "商户": "杨柳青民俗文化馆",   # ← 从文案内容提取
    "商品名称": "《吉祥如意》沉浸式戏剧体验",  # ← 从标题和内容提取
    "景点名称": ["杨柳青古镇", "杨柳青民俗文化馆"],  # ← 从文案提取
    "地点信息": ["天津", "西青", "杨柳青古镇"],      # ← 从标签和内容提取
    "服务内容": ["沉浸式戏剧体验", "解谜任务", ...], # ← 从文案描述提取
    "其他关键词": ["穿越时空", "沉浸式体验", ...]    # ← 从文案和标签提取
}
```

### 5. 验证和保存
```python
# 验证AI是否真的填补了所有空字段
for field in empty_fields:
    if not filled_data.get(field):  # 如果仍然为空
        # 使用默认值填补
        filled_data[field] = default_value

# 更新JSON文件中的对应项目
data[i] = filled_data

# 保存整个文件
json.dump(data, f, ensure_ascii=False, indent=2)
```

## 核心特点

1. **一对一映射**：JSON中的每个`id`都对应`data/文件夹/`下的同名文件
2. **智能分析**：AI读取原始文案的完整内容，而不是JSON中已经截断的`original_text`
3. **逐项处理**：每个项目单独处理，确保精确性
4. **多重保障**：AI填补 + 验证 + 默认值兜底

## 文件对应关系示例

```
cleaned_data/cultural_cleaned.json 中的项目:
├── "id": "debug_post_1.txt"   → data/cultural/debug_post_1.txt
├── "id": "debug_post_2.txt"   → data/cultural/debug_post_2.txt
├── "id": "debug_post_105.txt" → data/cultural/debug_post_105.txt
└── ...

cleaned_data/family_cleaned.json 中的项目:
├── "id": "debug_post_1.txt"   → data/family/debug_post_1.txt
├── "id": "debug_post_2.txt"   → data/family/debug_post_2.txt
└── ...
```

这样确保了每个空缺都能根据其对应的原始文案内容进行精准填补！ 