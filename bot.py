import base64
import json
import os
import random
import time
import urllib.parse
import requests

# --- LẤY KEY TỪ MÔI TRƯỜNG GITHUB SECRETS ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = "37602922189321771" # ID thì cứ để công khai không sao

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
    state = {"msg_count": 1, "drawn_cards": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content and content.strip():
                    state = json.loads(content)
        except Exception as e:
            print(f"⚠️ File trạng thái lỗi ({e}), khởi tạo lại...")
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

def sinh_noi_dung_va_prompt(chosen_card, is_conditional_style=False):
    print(f"1/4. Đang nhờ Gemini viết thông điệp cho lá {chosen_card}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json",
    }

    if is_conditional_style:
        prompt_style = f"""
        Tôi vừa bốc được lá Tarot: '{chosen_card}'.
        Hãy viết caption dạng tình huống/cảm xúc ngắn gọn theo mẫu:
        "Nếu hôm nay bạn [điền 1 cảm xúc/tình huống thực tế mà người đọc đang gặp phải], thì lá bài {chosen_card} muốn nhắn với bạn rằng [lời khuyên/thông điệp ngắn gọn tối đa 2 câu]."
        
        Trả về đúng định dạng JSON:
        {{
            "message": "Viết theo đúng mẫu câu trên, ngắn gọn, tự nhiên, chạm tới cảm xúc.",
            "image_prompt": "An artistic close-up photograph of a real vintage tarot card ({chosen_card}) lying gracefully on a cozy, bohemian patterned woven rug, warm ambient moody lighting, highly detailed fabric texture, photorealistic, aesthetic."
        }}
        """
    else:
        prompt_style = f"""
        Tôi vừa bốc được lá Tarot: '{chosen_card}'.
        Hãy viết caption ngắn gọn (tối đa 3 câu) giới thiệu năng lượng của lá {chosen_card} và đưa ra 1 lời khuyên thực tế.
        
        Trả về đúng định dạng JSON:
        {{
            "message": "Nội dung thông điệp ngắn gọn.",
            "image_prompt": "An artistic close-up photograph of a real vintage tarot card ({chosen_card}) lying gracefully on a cozy, bohemian patterned woven rug, warm ambient moody lighting, highly detailed fabric texture, photorealistic, aesthetic."
        }}
        """

    data = {
        "contents": [{"parts": [{"text": prompt_style}]}],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        res_json = response.json()

        if "candidates" not in res_json:
            print("❌ Gemini trả về lỗi:", res_json)
            return None, None

        content = res_json["candidates"][0]["content"]["parts"][0]["text"]
        data_json = json.loads(content)
        
        message = data_json.get("message", f"Lá bài {chosen_card} mang đến thông điệp dành cho bạn ngày hôm nay.")
        image_prompt = data_json.get("image_prompt", f"An artistic close-up photograph of a real vintage tarot card ({chosen_card}) lying gracefully on a cozy, bohemian patterned woven rug, warm ambient moody lighting, highly detailed fabric texture, photorealistic, aesthetic.")

        return message, image_prompt
    except Exception as e:
        print("Lỗi xử lý dữ liệu từ Gemini:", e)
        return None, None

def tao_va_up_anh(image_prompt):
    print("2/4. Đang vẽ ảnh thực tế nghệ thuật bằng Pollinations (Flux)...")
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

if __name__ == "__main__":
    # Check xem có thiếu API Key không
    if not GEMINI_API_KEY or not IMGBB_API_KEY or not THREADS_ACCESS_TOKEN:
        print("❌ Thiếu API Key! Hãy kiểm tra lại cấu hình môi trường (GitHub Secrets).")
        exit(1)

    chosen_card, current_state = quan_ly_trang_thai()
    msg_num = current_state["msg_count"]

    # Bài chẵn viết kiểu "Nếu hôm nay bạn...", bài lẻ viết "Thông điệp..."
    is_conditional = (msg_num % 2 == 0)

    ai_msg, img_prompt = sinh_noi_dung_va_prompt(chosen_card, is_conditional_style=is_conditional)

    if ai_msg and img_prompt:
        if is_conditional:
            prefix = ""
        else:
            prefix = f"Thông điệp số {msg_num:02d}: "
            
        suffix = "\n\n🫣 [Phần được tiết lộ]: Ghé ngay website tavanrot.online để xem chúng tôi có đọc được năng lượng của bạn không."
        
        # Giới hạn 495 ký tự tối đa của Threads
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
