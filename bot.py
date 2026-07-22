import requests
import json
import urllib.parse
import time
import random
import base64
import re
import os

# --- ĐIỀN 3 KEY CÒN LẠI VÀO ĐÂY ---
import requests
import json
import urllib.parse
import time
import random
import base64
import re
import os
from datetime import datetime, timezone, timedelta

# --- ĐIỀN 3 KEY CÒN LẠI VÀO ĐÂY ---
IMGBB_API_KEY = "0cc7bd6394a548f1651e1feb9fa437b5"
THREADS_ACCESS_TOKEN = "THAAMreyEmvaVBYlkyV1cxbEZAtR1lPQXg0YVJ5S2dWMDFGRDNaZAFd6cmtIUC1wR1psOTM4cVNVZAHhKNzQtczVZAN1FvcnNYdzJLbGtSR2hNMnMwNkFuOHY1S3h2ZAXg4MDRsaHlOQ201RnlqaVdLSDRwZAy03SEtFVmNTRGkyd2JYSVhsdVpyNVVNNS1jZAGp6M3cZD"
THREADS_USER_ID = "37602922189321771"

# Key OpenRouter của mày (Đã Base64)
OPENROUTER_KEY_B64 = "c2stb3ItdjEtMmUxYzE4OWQ0MGE5MzgzYmY0NjkyMzRjNTQwMDM2ZTU0NjAyZmY0MDM5ZmNiYWU4MjAyYTdkODc2Mzc3ZDg1NA==" 
OPENROUTER_API_KEY = base64.b64decode(OPENROUTER_KEY_B64).decode('utf-8')

# --- DANH SÁCH 78 LÁ BÀI TAROT ---
TAROT_DECK = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Hierophant", 
    "The Lovers", "The Chariot", "Strength", "The Hermit", "Wheel of Fortune", "Justice", "The Hanged Man", 
    "Death", "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World",
    "Ace of Wands", "Two of Wands", "Three of Wands", "Four of Wands", "Five of Wands", "Six of Wands", "Seven of Wands", "Eight of Wands", "Nine of Wands", "Ten of Wands", "Page of Wands", "Knight of Wands", "Queen of Wands", "King of Wands",
    "Ace of Cups", "Two of Cups", "Three of Cups", "Four of Cups", "Five of Cups", "Six of Cups", "Seven of Cups", "Eight of Cups", "Nine of Cups", "Ten of Cups", "Page of Cups", "Knight of Cups", "Queen of Cups", "King of Cups",
    "Ace of Swords", "Two of Swords", "Three of Swords", "Four of Swords", "Five of Swords", "Six of Swords", "Seven of Swords", "Eight of Swords", "Nine of Swords", "Ten of Swords", "Page of Swords", "Knight of Swords", "Queen of Swords", "King of Swords",
    "Ace of Pentacles", "Two of Pentacles", "Three of Pentacles", "Four of Pentacles", "Five of Pentacles", "Six of Pentacles", "Seven of Pentacles", "Eight of Pentacles", "Nine of Pentacles", "Ten of Pentacles", "Page of Pentacles", "Knight of Pentacles", "Queen of Pentacles", "King of Pentacles"
]

STATE_FILE = "tarot_state.json"

def get_vietnam_hour():
    vn_tz = timezone(timedelta(hours=7))
    return datetime.now(vn_tz).hour

def is_peak_hour(hour):
    # Từ 5h đến 23h là 3 bài/tiếng, còn lại 2 bài/tiếng
    return 5 <= hour < 23

def quan_ly_trang_thai():
    # Reset hoặc khởi tạo mới từ số 01
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {"msg_count": 1, "drawn_cards": []}
    
    available_cards = [card for card in TAROT_DECK if card not in state["drawn_cards"]]
    
    if not available_cards:
        print("🔄 Đã bốc hết 78 lá. Đang xào bài lại từ đầu...")
        state["drawn_cards"] = []
        available_cards = TAROT_DECK
        
    chosen_card = random.choice(available_cards)
    return chosen_card, state

def cap_nhat_trang_thai(state, chosen_card):
    state["drawn_cards"].append(chosen_card)
    state["msg_count"] += 1
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def sinh_noi_dung_va_prompt(chosen_card):
    print(f"1/4. Đang nhờ OpenRouter viết thông điệp cho lá {chosen_card}...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Tôi vừa bốc được lá bài Tarot: '{chosen_card}'.
    Hãy viết caption theo cấu trúc: Mở đầu giới thiệu ngắn gọn, cuốn hút về năng lượng của lá {chosen_card}, sau đó đưa ra 1 thông điệp và lời khuyên nhỏ, thực tế cho người đọc.
    Trả về cho tôi ĐÚNG ĐỊNH DẠNG JSON sau, không kèm text nào khác:
    {{
        "message": "Viết ngắn gọn (tối đa 3 câu), mở bài giới thiệu lá {chosen_card} và kèm lời khuyên nhỏ.",
        "image_prompt": "A clean, realistic top-down photo of a real vintage tarot card ({chosen_card}) placed naturally on a rustic wooden floor next to a cozy rug, warm lighting, simple, authentic, photorealistic."
    }}
    """
    data = {
        "model": "openrouter/auto", 
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        content = response.json()['choices'][0]['message']['content']
        
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if not match:
            return None, None
            
        data_json = json.loads(match.group(0))
        message = data_json.get('message', f"Lá bài {chosen_card} xuất hiện mang theo năng lượng mới, hãy đón nhận mọi thứ thật bình thản.")
        image_prompt = data_json.get('image_prompt', f"A clean, realistic top-down photo of a real vintage tarot card ({chosen_card}) placed naturally on a rustic wooden floor next to a cozy rug, warm lighting, simple, authentic, photorealistic.")
        
        return message, image_prompt
    except Exception as e:
        print("Lỗi đọc data từ OpenRouter:", e)
        return None, None

def tao_va_up_anh(image_prompt):
    print("2/4. Đang vẽ ảnh thực tế bằng Pollinations (Flux)...")
    seed = random.randint(1, 999999)
    encoded_prompt = urllib.parse.quote(image_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&nologo=true&seed={seed}"
    
    img_response = requests.get(image_url)
    
    print("3/4. Đang up ảnh lên ImgBB lấy link public...")
    imgbb_url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": IMGBB_API_KEY,
        "image": base64.b64encode(img_response.content)
    }
    res = requests.post(imgbb_url, data=payload).json()
    return res['data']['url']

def dang_bai_len_threads(final_caption, image_url):
    print("4/4. Đang gửi bài lên Threads...")
    url_container = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    params = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": final_caption,
        "access_token": THREADS_ACCESS_TOKEN
    }
    res_container = requests.post(url_container, params=params).json()
    container_id = res_container.get('id')
    
    if not container_id:
        print("❌ Lỗi tạo container:", res_container)
        return False

    print("=> Chờ Meta xử lý ảnh 15s...")
    time.sleep(15)
    
    url_publish = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    res_publish = requests.post(url_publish, params={
        "creation_id": container_id,
        "access_token": THREADS_ACCESS_TOKEN
    }).json()
    
    if res_publish.get('id'):
        print("\n✅ ĐÃ ĐĂNG THÀNH CÔNG!")
        return True
    else:
        print("❌ Lỗi publish:", res_publish)
        return False

# --- LUỒNG CHẠY CHÍNH ---
if __name__ == "__main__":
    current_hour = get_vietnam_hour()
    peak = is_peak_hour(current_hour)
    so_bai = 3 if peak else 2
    
    print(f"Giờ VN: {current_hour}h | Cao điểm (5h-23h): {peak} | Số bài cần đăng trong giờ này: {so_bai}")
    
    for i in range(so_bai):
        print(f"\n--- TIẾN TRÌNH BÀI THỨ {i+1}/{so_bai} ---")
        chosen_card, current_state = quan_ly_trang_thai()
        msg_num = current_state["msg_count"]
        
        ai_msg, img_prompt = sinh_noi_dung_va_prompt(chosen_card)
        
        if ai_msg and img_prompt:
            prefix = f"Thông điệp số {msg_num:02d}: "
            suffix = "\n\nMuốn biết thêm thì ghé tavanrot.online nhé!"
            
            max_ai_len = 495 - len(prefix) - len(suffix)
            if len(ai_msg) > max_ai_len:
                ai_msg = ai_msg[:max_ai_len-3].strip() + "..."
                
            final_caption = prefix + ai_msg + suffix
            print(f"\n--- CAPTION ({len(final_caption)} ký tự) ---\n{final_caption}\n")
            
            link_anh = tao_va_up_anh(img_prompt)
            success = dang_bai_len_threads(final_caption, link_anh)
            
            if success:
                cap_nhat_trang_thai(current_state, chosen_card)
                print(f"=> Đã lưu trạng thái: Lá {chosen_card} vào sổ tay.")
                
        # Nghỉ giữa các bài trong tiếng
        if i < so_bai - 1:
            delay_minutes = random.randint(18, 20) if peak else random.randint(25, 30)
            print(f"Đợi {delay_minutes} phút trước bài tiếp theo...")
            time.sleep(delay_minutes * 60)

# Key OpenRouter của mày (Đã Base64)
OPENROUTER_KEY_B64 = "c2stb3ItdjEtMmUxYzE4OWQ0MGE5MzgzYmY0NjkyMzRjNTQwMDM2ZTU0NjAyZmY0MDM5ZmNiYWU4MjAyYTdkODc2Mzc3ZDg1NA==" 
OPENROUTER_API_KEY = base64.b64decode(OPENROUTER_KEY_B64).decode('utf-8')

# --- DANH SÁCH 78 LÁ BÀI TAROT ---
TAROT_DECK = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Hierophant", 
    "The Lovers", "The Chariot", "Strength", "The Hermit", "Wheel of Fortune", "Justice", "The Hanged Man", 
    "Death", "Temperance", "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World",
    "Ace of Wands", "Two of Wands", "Three of Wands", "Four of Wands", "Five of Wands", "Six of Wands", "Seven of Wands", "Eight of Wands", "Nine of Wands", "Ten of Wands", "Page of Wands", "Knight of Wands", "Queen of Wands", "King of Wands",
    "Ace of Cups", "Two of Cups", "Three of Cups", "Four of Cups", "Five of Cups", "Six of Cups", "Seven of Cups", "Eight of Cups", "Nine of Cups", "Ten of Cups", "Page of Cups", "Knight of Cups", "Queen of Cups", "King of Cups",
    "Ace of Swords", "Two of Swords", "Three of Swords", "Four of Swords", "Five of Swords", "Six of Swords", "Seven of Swords", "Eight of Swords", "Nine of Swords", "Ten of Swords", "Page of Swords", "Knight of Swords", "Queen of Swords", "King of Swords",
    "Ace of Pentacles", "Two of Pentacles", "Three of Pentacles", "Four of Pentacles", "Five of Pentacles", "Six of Pentacles", "Seven of Pentacles", "Eight of Pentacles", "Nine of Pentacles", "Ten of Pentacles", "Page of Pentacles", "Knight of Pentacles", "Queen of Pentacles", "King of Pentacles"
]

STATE_FILE = "tarot_state.json"

def quan_ly_trang_thai():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {"msg_count": 1, "drawn_cards": []}
    
    available_cards = [card for card in TAROT_DECK if card not in state["drawn_cards"]]
    
    if not available_cards:
        print("🔄 Đã bốc hết 78 lá. Đang xào bài lại từ đầu...")
        state["drawn_cards"] = []
        available_cards = TAROT_DECK
        
    chosen_card = random.choice(available_cards)
    return chosen_card, state

def cap_nhat_trang_thai(state, chosen_card):
    state["drawn_cards"].append(chosen_card)
    state["msg_count"] += 1
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def sinh_noi_dung_va_prompt(chosen_card):
    print(f"1/4. Đang nhờ OpenRouter (Auto) viết thông điệp cho lá {chosen_card}...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prompt mới: Mở bài giới thiệu lá bài + thông điệp nhỏ gọn + prompt ảnh thực tế đơn giản
    prompt = f"""
    Tôi vừa bốc được lá bài Tarot: '{chosen_card}'.
    Hãy viết caption theo cấu trúc: Mở đầu giới thiệu ngắn gọn về năng lượng của lá {chosen_card}, sau đó đưa ra 1 thông điệp và lời khuyên nhỏ, thực tế cho người đọc.
    Trả về cho tôi ĐÚNG ĐỊNH DẠNG JSON sau, không kèm text nào khác:
    {{
        "message": "Viết ngắn gọn (tối đa 3 câu), mở bài giới thiệu lá {chosen_card} và kèm lời khuyên nhỏ.",
        "image_prompt": "A clean, realistic top-down photo of a real vintage tarot card ({chosen_card}) placed naturally on a rustic wooden floor next to a cozy rug, warm lighting, simple, authentic, photorealistic."
    }}
    """
    data = {
        "model": "openrouter/auto", 
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        content = response.json()['choices'][0]['message']['content']
        
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if not match:
            return None, None
            
        data_json = json.loads(match.group(0))
        message = data_json.get('message', f"Lá bài {chosen_card} xuất hiện mang theo năng lượng mới, hãy đón nhận mọi thứ thật bình thản.")
        image_prompt = data_json.get('image_prompt', f"A clean, realistic top-down photo of a real vintage tarot card ({chosen_card}) placed naturally on a rustic wooden floor next to a cozy rug, warm lighting, simple, authentic, photorealistic.")
        
        return message, image_prompt
    except Exception as e:
        print("Lỗi đọc data từ OpenRouter:", e)
        return None, None

def tao_va_up_anh(image_prompt):
    print("2/4. Đang vẽ ảnh thực tế bằng Pollinations (Flux)...")
    seed = random.randint(1, 999999)
    encoded_prompt = urllib.parse.quote(image_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&nologo=true&seed={seed}"
    
    img_response = requests.get(image_url)
    
    print("3/4. Đang up ảnh lên ImgBB lấy link public...")
    imgbb_url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": IMGBB_API_KEY,
        "image": base64.b64encode(img_response.content)
    }
    res = requests.post(imgbb_url, data=payload).json()
    return res['data']['url']

def dang_bai_len_threads(final_caption, image_url):
    print("4/4. Đang gửi bài lên Threads...")
    url_container = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    params = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": final_caption,
        "access_token": THREADS_ACCESS_TOKEN
    }
    res_container = requests.post(url_container, params=params).json()
    container_id = res_container.get('id')
    
    if not container_id:
        print("❌ Lỗi tạo container:", res_container)
        return False

    print("=> Chờ Meta xử lý ảnh 15s...")
    time.sleep(15)
    
    url_publish = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    res_publish = requests.post(url_publish, params={
        "creation_id": container_id,
        "access_token": THREADS_ACCESS_TOKEN
    }).json()
    
    if res_publish.get('id'):
        print("\n✅ ĐÃ ĐĂNG THÀNH CÔNG!")
        return True
    else:
        print("❌ Lỗi publish:", res_publish)
        return False

# --- LUỒNG CHẠY CHÍNH ---
if __name__ == "__main__":
    chosen_card, current_state = quan_ly_trang_thai()
    msg_num = current_state["msg_count"]
    
    ai_msg, img_prompt = sinh_noi_dung_va_prompt(chosen_card)
    
    if ai_msg and img_prompt:
        prefix = f"Thông điệp số {msg_num:02d}: "
        suffix = "\n\nMuốn biết thêm thì ghé tavanrot.online nhé!"
        
        max_ai_len = 495 - len(prefix) - len(suffix)
        if len(ai_msg) > max_ai_len:
            ai_msg = ai_msg[:max_ai_len-3].strip() + "..."
            
        final_caption = prefix + ai_msg + suffix
        print(f"\n--- CAPTION CHUẨN BỊ ĐĂNG ({len(final_caption)} ký tự) ---\n{final_caption}\n")
        
        link_anh = tao_va_up_anh(img_prompt)
        success = dang_bai_len_threads(final_caption, link_anh)
        
        if success:
            cap_nhat_trang_thai(current_state, chosen_card)
            print(f"=> Đã lưu trạng thái: Lá {chosen_card} vào sổ tay.")