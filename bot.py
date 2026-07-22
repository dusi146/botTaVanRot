import re
import base64
import json
import os
import random
import time
import urllib.parse
import requests
from datetime import date

# --- LẤY KEY TỪ MÔI TRƯỜNG GITHUB SECRETS ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = "37602922189321771"

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
    today_str = date.today().isoformat()
    # Khởi tạo mặc định
    state = {"date": today_str, "deep_count": 0, "total_posts": 0}
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content and content.strip():
                    loaded_state = json.loads(content)
                    # Nếu sang ngày mới -> reset deep_count về 0
                    if loaded_state.get("date") != today_str:
                        state["total_posts"] = loaded_state.get("total_posts", 0)
                    else:
                        state = loaded_state
        except Exception as e:
            print(f"⚠️ File trạng thái lỗi ({e}), khởi tạo lại...")

    # Bốc ngẫu nhiên 1, 2, hoặc 3 lá (Tỉ lệ: 70% 1 lá, 20% 2 lá, 10% 3 lá)
    num_cards = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
    chosen_cards = random.sample(TAROT_DECK, num_cards)
    
    return chosen_cards, state

def cap_nhat_trang_thai(state, is_deep):
    state["total_posts"] += 1
    if is_deep:
        state["deep_count"] += 1
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def sinh_noi_dung(chosen_cards, is_deep_message=True):
    cards_str = ", ".join(chosen_cards)
    print(f"1/4. Đang nhờ OpenRouter viết cho: {cards_str}...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    if is_deep_message:
        prompt_style = f"""
        Tôi vừa bốc được các lá Tarot: {cards_str}.
        Hãy viết một đoạn thông điệp ngắn gọn (tối đa 3 câu) giới thiệu năng lượng kết hợp của các lá này và đưa ra 1 lời khuyên thực tế.
        Trả về đúng định dạng JSON: {{"message": "Nội dung..."}}
        """
    else:
        prompt_style = f"""
        Tôi vừa bốc được các lá Tarot: {cards_str}.
        Hãy viết caption dạng tình huống ngắn gọn theo mẫu:
        "Nếu hôm nay bạn [điền 1 cảm xúc/tình huống], thì các lá bài {cards_str} muốn nhắn với bạn rằng [lời khuyên tối đa 2 câu]."
        Trả về đúng định dạng JSON: {{"message": "Nội dung..."}}
        """

    data = {
        "model": "google/gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt_style}],
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        res_json = response.json()
        if "choices" not in res_json:
            return None
        content = res_json["choices"][0]["message"]["content"]
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0)).get("message")
        return None
    except Exception as e:
        print("Lỗi OpenRouter:", e)
        return None

def tao_va_up_anh(chosen_cards):
    count = len(chosen_cards)
    names = ", ".join(chosen_cards)
    
    print("2/4. Đang xử lý ảnh...")
    image_bytes = None
    
    # 1. THỬ TẠO ẢNH BẰNG GOOGLE IMAGEN 3 TRƯỚC
    imagen_prompt = f"A highly detailed, ultra-realistic overhead macro photograph of {count} tarot cards lying organically on an antique, richly patterned Persian woven rug. The specific cards are: {names}. The cards are authentic Rider-Waite-Smith style, featuring accurate artwork, vivid symbolism, textured thick cardstock, and slightly worn edges indicating frequent use. They are placed distinctly without overlapping the main illustrations. The scene is illuminated by warm, cinematic ambient lighting with soft shadows, highlighting the tactile fabric texture of the rug. 8K resolution, masterpiece, professional studio photography, shallow depth of field focusing on the cards."
    
    try:
        imagen_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"
        payload = {
            "instances": [{"prompt": imagen_prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "1:1"}
        }
        res_imagen = requests.post(imagen_url, json=payload).json()
        if "predictions" in res_imagen:
            print("✅ Đã tạo ảnh thành công bằng Google Imagen 3.")
            image_bytes = base64.b64decode(res_imagen["predictions"][0]["bytesBase64Encoded"])
        else:
            print("⚠️ Google Imagen 3 từ chối (Lỗi hoặc vi phạm chính sách). Chuyển sang Pollinations...")
    except Exception as e:
        print("⚠️ Lỗi gọi Google API, chuyển sang Pollinations:", e)

    # 2. NẾU GOOGLE LỖI, DÙNG POLLINATIONS LÀM FALLBACK
    if not image_bytes:
        flux_prompt = f"Photorealistic top-down view of {count} tarot cards ({names}) on elegant vintage Persian rug, Rider-Waite style artwork, realistic paper texture, worn edges, warm cinematic lighting, woven fabric texture, mystical atmosphere, macro photography, 8K, HDR, highly detailed, perfectly separated cards."
        seed = random.randint(1, 999999)
        encoded_prompt = urllib.parse.quote(flux_prompt)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&nologo=true&seed={seed}"
        
        try:
            img_response = requests.get(pollinations_url, timeout=60)
            if img_response.status_code == 200:
                print("✅ Đã tạo ảnh thành công bằng Pollinations (Flux).")
                image_bytes = img_response.content
            else:
                return None
        except Exception as e:
            print("❌ Lỗi Pollinations:", e)
            return None

    # 3. UP ẢNH LÊN IMGBB
    print("3/4. Đang up ảnh lên ImgBB...")
    try:
        imgbb_url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(image_bytes),
        }
        res_bb = requests.post(imgbb_url, data=payload).json()
        if "data" in res_bb and "url" in res_bb["data"]:
            return res_bb["data"]["url"]
        else:
            print("❌ Lỗi ImgBB:", res_bb)
            return None
    except Exception as e:
        print("❌ Lỗi up ảnh ImgBB:", e)
        return None

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
    if not OPENROUTER_API_KEY or not GEMINI_API_KEY or not IMGBB_API_KEY or not THREADS_ACCESS_TOKEN:
        print("❌ Thiếu API Key! Hãy kiểm tra lại cấu hình môi trường.")
        exit(1)
        
    chosen_cards, current_state = quan_ly_trang_thai()
    
    # Xét xem bài này có phải bài Deep Message không (2 bài/ngày)
    is_deep = (current_state["deep_count"] < 2)
    
    ai_msg = sinh_noi_dung(chosen_cards, is_deep_message=is_deep)

    if ai_msg:
        prefix = f"Thông điệp số {current_state['total_posts'] + 1}: " if is_deep else ""
        suffix = "\n\nGhé ngay website tavanrot.online để xem chúng tôi có đọc được năng lượng của bạn không."
        
        # Cắt bớt nếu quá 495 ký tự
        max_ai_len = 495 - len(prefix) - len(suffix)
        if len(ai_msg) > max_ai_len:
            ai_msg = ai_msg[:max_ai_len-3].strip() + "..."
            
        final_caption = prefix + ai_msg + suffix
        print(f"\n--- CAPTION CHUẨN BỊ ĐĂNG ---\n{final_caption}\n")
        
        link_anh = tao_va_up_anh(chosen_cards)
        if link_anh:
            success = dang_bai_len_threads(final_caption, link_anh)
            if success:
                cap_nhat_trang_thai(current_state, is_deep)
                print(f"=> Đã lưu trạng thái bài đăng.")
        else:
            print("⚠️ Bỏ qua đợt đăng này do không tạo/up được ảnh.")
