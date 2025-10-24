import yaml
import sys
from dateutil import parser
import pytz
from pytz import timezone, exceptions as pytz_exceptions
from urllib.parse import urlparse
import os
import re

# 退出码
EXIT_CODE_ERROR = 1

def check_activity_structure(activity, file_path):
    """检查单个活动（Activity）条目的结构和中文规范。"""
    required_fields = ['title', 'description', 'category', 'tags', 'events']
    
    for field in required_fields:
        if field not in activity:
            print(f"Error: Missing required field '{field}' in an activity in {file_path}")
            sys.exit(EXIT_CODE_ERROR)

    # 规范 1: category 必须是 conference, competition, 或 activity
    valid_categories = ['competition', 'conference', 'activity']
    if activity['category'] not in valid_categories:
        print(f"Error: Invalid category '{activity['category']}' in {file_path}. "
              f"规范要求: 必须是 {', '.join(valid_categories)}。")
        sys.exit(EXIT_CODE_ERROR)

    if not isinstance(activity.get('tags'), list):
        print(f"Error: 'tags' should be a list in {file_path}")
        sys.exit(EXIT_CODE_ERROR)

    events = activity.get('events', [])
    if not isinstance(events, list):
        print(f"Error: 'events' should be a list in {file_path}")
        sys.exit(EXIT_CODE_ERROR)

    for event in events:
        check_event_structure(event, file_path)

def check_event_structure(event, file_path):
    """检查单个事件（Event）条目的结构和中文规范。"""
    required_fields = ['year', 'id', 'link', 'timeline', 'timezone', 'date', 'place']
    
    for field in required_fields:
        if field not in event:
            print(f"Error: Missing required field '{field}' in an event in {file_path}")
            sys.exit(EXIT_CODE_ERROR)

    # 检查 link (URL) 格式
    try:
        parsed_url = urlparse(event['link'])
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL structure")
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid URL '{event['link']}' in {file_path}. Details: {e}")
        sys.exit(EXIT_CODE_ERROR)

    # 规范 3: timezone 必须是标准的 IANA 时区名称，并获取 pytz 时区对象
    event_tz = None
    try:
        event_tz = timezone(event['timezone'])
    except pytz_exceptions.UnknownTimeZoneError:
        print(f"Error: Invalid timezone '{event['timezone']}' in {file_path}. "
              f"规范要求: 请使用标准的 IANA 时区名称 (例如 Asia/Shanghai)。")
        sys.exit(EXIT_CODE_ERROR)
    except TypeError:
        print(f"Error: 'timezone' must be a string in {file_path}")
        sys.exit(EXIT_CODE_ERROR)

    timeline = event.get('timeline', [])
    if not isinstance(timeline, list) or not timeline:
        print(f"Error: 'timeline' should be a non-empty list in {file_path}")
        sys.exit(EXIT_CODE_ERROR)
        
    # 规范 4: date 字段格式（基础可读性检查）
    date_str = event['date']
    # 检查日期范围是否包含中文 "年", "月", "日" 和数字
    if not re.search(r'\d{4} *年 *\d+ *月 *\d+ *日', date_str):
        print(f"Warning: 'date' field format might be incorrect in {file_path} for event '{event['id']}'. "
              f"规范要求: 请使用人类可读的格式，如 '2025 年 4 月 30 日' 或 '2025 年 4 月 30 日 - 9 月 30 日'。")
    
    # 规范 5: place 字段格式
    place_str = event['place']
    if not isinstance(place_str, str) or not place_str.strip():
        print(f"Error: 'place' field cannot be empty in {file_path} for event '{event['id']}'.")
        sys.exit(EXIT_CODE_ERROR)
    
    # 检查 deadline 格式和时序 (使用 event_tz 进行统一比较)
    last_deadline_aware = None
    for item in timeline:
        if not isinstance(item, dict) or 'deadline' not in item or 'comment' not in item:
            print(f"Error: timeline item in {file_path} is invalid or missing 'deadline' or 'comment'")
            sys.exit(EXIT_CODE_ERROR)
        
        deadline_str = item['deadline']
        
        # 规范 2: deadline 必须是 YYYY-MM-DDTHH:mm:ss 格式
        try:
            current_deadline = parser.isoparse(deadline_str)
            
            # --- START: Custom logic for Naive Deadline ---
            # 检查是否有时区信息（允许非时区感知 (Naive) 的时间，不发出警告）
            if current_deadline.tzinfo is None or current_deadline.tzinfo.utcoffset(current_deadline) is None:
                # 警告语句已移除，但逻辑保留：使用 event['timezone'] 字段进行本地化
                current_deadline_aware = event_tz.localize(current_deadline)
            else:
                # 如果时间已经是 Aware 的，我们将其转换为 event 的指定时区
                current_deadline_aware = current_deadline.astimezone(event_tz)
            # --- END: Custom logic for Naive Deadline ---
            
            # 检查时序
            if last_deadline_aware is not None and current_deadline_aware < last_deadline_aware:
                print(f"Error: timeline in {file_path} for event '{event['id']}' is not sorted chronologically. "
                      f"Deadline '{deadline_str}' is logically before the previous deadline.")
                sys.exit(EXIT_CODE_ERROR)
                
            # 更新上一个截止日期，用于下一次比较
            last_deadline_aware = current_deadline_aware
            
        except ValueError as e:
            # 捕获 ISO 8601 格式错误 (例如 T24:00:00)
            print(f"Error: Invalid ISO 8601 format for deadline '{deadline_str}' in {file_path}. "
                  f"规范要求: 请使用 YYYY-MM-DDTHH:mm:ss 格式，并确保时间合法。Details: {e}")
            sys.exit(EXIT_CODE_ERROR)

# ------------------------------------------------------------------------------------------------ #
## Main 逻辑
# ------------------------------------------------------------------------------------------------ #

def main():
    data_dir = os.path.join(os.getcwd(), 'data')
    
    if not os.path.isdir(data_dir):
        print(f"Fatal Error: Data directory not found at '{data_dir}'. Ensure you are running the script from the project root.")
        sys.exit(EXIT_CODE_ERROR)
        
    # 仅查找 .yml 或 .yaml 文件
    data_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(('.yml', '.yaml'))]
    
    if not data_files:
        print(f"Warning: No YAML files found in the '{data_dir}' directory.")
        return

    all_event_ids = set()
    all_tags = set()

    for file_path in data_files:
        print(f"Checking {os.path.relpath(file_path)}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file_path}: {e}")
            sys.exit(EXIT_CODE_ERROR)
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            sys.exit(EXIT_CODE_ERROR)

        if not isinstance(data, list):
            print(f"Error: {file_path} should contain a top-level list of activities.")
            sys.exit(EXIT_CODE_ERROR)

        for item in data:
            if not isinstance(item, dict):
                print(f"Error: All top-level items in {file_path} must be dictionaries (activities).")
                sys.exit(EXIT_CODE_ERROR)
                
            check_activity_structure(item, file_path)

            for event in item.get('events', []):
                if 'id' in event:
                    event_id = event['id']
                    if event_id in all_event_ids:
                        print(f"Error: Duplicate event ID '{event_id}' found. First occurrence in another file/activity.")
                        sys.exit(EXIT_CODE_ERROR)
                    all_event_ids.add(event_id)
            
            for tag in item.get('tags', []):
                if isinstance(tag, str):
                    all_tags.add(tag)
                else:
                    print(f"Warning: Non-string tag '{tag}' found in {file_path}. Skipping.")

    # Check for similar tags (case-insensitive)
    lower_to_original = {}
    for tag in all_tags:
        lower_tag = tag.lower()
        if lower_tag in lower_to_original and lower_to_original[lower_tag] != tag:
            print(f"Warning: Possible case-insensitive duplicate tags found: '{lower_to_original[lower_tag]}' and '{tag}'")
        else:
            lower_to_original[lower_tag] = tag

    print("\n✅ All data files passed validation.")

if __name__ == "__main__":
    main()
