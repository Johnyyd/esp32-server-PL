import datetime
import httpx
from app.core.config import settings

def get_time():
    """Lấy thời gian hiện tại."""
    now = datetime.datetime.now()
    return f"Bây giờ là {now.strftime('%H:%M:%S, ngày %d/%m/%Y')}."

def get_date_info():
    """Lấy thông tin ngày tháng, thứ trong tuần."""
    now = datetime.datetime.now()
    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday_str = weekdays[now.weekday()]
    return f"Hôm nay là {weekday_str}, ngày {now.day} tháng {now.month} năm {now.year}."

import random
def tell_joke():
    """Kể một câu chuyện cười."""
    jokes = [
        "Có một con heo đi qua đường, sau đó không còn con heo nào đi qua đường nữa vì nó đi qua rồi.",
        "Tại sao biển lại mặn? Vì người ta khóc nhiều quá.",
        "Tại sao viên bi lại tròn? Vì nếu vuông thì gọi là cục rồi.",
        "Bác sĩ nói với bệnh nhân: Anh bị béo phì. Bệnh nhân hỏi: Làm sao để chữa? Bác sĩ đáp: Lắc đầu mỗi khi có ai mời ăn."
    ]
    return random.choice(jokes)

async def get_weather(location: str, date: str = None):
    """Lấy thông tin thời tiết cho một khu vực."""
    if date:
        return f"Thời tiết tại {location} vào ngày {date} hiện đang có nắng, nhiệt độ khoảng 28 độ C."
    return f"Thời tiết tại {location} hiện đang có nắng, nhiệt độ khoảng 28 độ C."

import asyncio
from ddgs import DDGS

async def search_news(query: str):
    """Tìm kiếm tin tức thời sự trực tuyến."""
    try:
        def fetch_news():
            return list(DDGS().news(query, max_results=5))
        
        results = await asyncio.to_thread(fetch_news)
        if not results:
            return f"Không tìm thấy tin tức nào về {query}."
        
        news_summary = ""
        for i, article in enumerate(results):
            news_summary += f"{i+1}. {article.get('title', '')} - {article.get('body', '')} - {article.get('source', '')}\n"
        
        return f"Tin tức thời sự về {query}:\n{news_summary}"
    except Exception as e:
        print("Lỗi khi tìm kiếm tin tức:", e)
        return "Lỗi khi tìm kiếm tin tức."

async def search_web(query: str):
    """Tìm kiếm thông tin chung trực tuyến."""
    try:
        def fetch_web():
            return list(DDGS().text(query, max_results=5))
        
        results = await asyncio.to_thread(fetch_web)
        if not results:
            return f"Không tìm thấy thông tin nào về {query}."
        
        web_summary = ""
        for i, article in enumerate(results):
            web_summary += f"{i+1}. {article.get('title', '')} - {article.get('body', '')}\n"
        
        return f"Thông tin web về {query}:\n{web_summary}"
    except Exception as e:
        print("Lỗi khi tìm kiếm web:", e)
        return "Lỗi khi tìm kiếm web."

async def get_sensor_data(sensor_id: str):
    """Đọc dữ liệu từ cảm biến ESP32 (vd: nhiet_do_phong, do_am_phong)."""
    url = f"http://{settings.ESP32_IP}/sensor/{sensor_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return f"Cảm biến {sensor_id} hiện tại là {data.get('value', 'không rõ')} {data.get('state', '')}"
            return f"Không đọc được cảm biến {sensor_id}, mã lỗi: {response.status_code}"
    except Exception as e:
        return f"Lỗi kết nối tới ESP32: {str(e)}"

async def control_switch(switch_id: str, command: str):
    """Điều khiển công tắc qua Home Assistant. Command là 'turn_on' hoặc 'turn_off'."""
    # Ánh xạ switch_id từ AI sang entity_id của HA
    entity_id = ""
    if switch_id == "turn_on_pc":
        entity_id = "switch.phong_ngu_esp32_s3_nut_nguon_pc"
    elif switch_id == "reset_pc":
        entity_id = "switch.phong_ngu_esp32_s3_nut_reset_pc"
    else:
        return f"Không tìm thấy công tắc {switch_id}"
        
    if not settings.HA_URL or not settings.HA_TOKEN:
        return "Lỗi: Chưa cấu hình HA_URL hoặc HA_TOKEN"
        
    url = f"{settings.HA_URL.rstrip('/')}/api/services/switch/{command}"
    headers = {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"entity_id": entity_id}
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"Calling HA API: {url} with entity_id: {entity_id}")
            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
            print(f"HA Response: {response.status_code} - {response.text}")
            if response.status_code in [200, 201]:
                return f"Đã thực hiện {command} trên PC thành công."
            return f"Lỗi HA: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Lỗi kết nối tới HA: {str(e)}"

async def control_light(light_id: str, command: str):
    """Điều khiển đèn qua Home Assistant. Command là 'turn_on' hoặc 'turn_off'."""
    if not settings.HA_URL or not settings.HA_TOKEN:
        return "Lỗi: Chưa cấu hình HA_URL hoặc HA_TOKEN"
        
    url = f"{settings.HA_URL.rstrip('/')}/api/services/light/{command}"
    headers = {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"entity_id": light_id}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
            if response.status_code in [200, 201]:
                return f"Đã thực hiện {command} trên đèn {light_id} thành công."
            return f"Lỗi HA: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Lỗi kết nối tới HA: {str(e)}"

async def control_servo(servo_id: str, level: float):
    """Điều khiển servo ESP32. Level từ -1.0 đến 1.0."""
    url = f"http://{settings.ESP32_IP}/servo/{servo_id}/set?level={level}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, timeout=5.0)
            if response.status_code == 200:
                return f"Đã đặt servo {servo_id} tới mức {level}."
            return f"Lỗi điều khiển servo {servo_id}, mã lỗi: {response.status_code}"
    except Exception as e:
        return f"Lỗi kết nối tới ESP32: {str(e)}"

async def wave_hands():
    """Điều khiển hai tay của ESP32 để vẫy chào."""
    if not settings.HA_URL or not settings.HA_TOKEN:
        return "Lỗi: Chưa cấu hình HA_URL hoặc HA_TOKEN"
        
    url = f"{settings.HA_URL.rstrip('/')}/api/services/button/press"
    headers = {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json"
    }
    # Dựa vào cách đặt tên thiết bị trước đó, nút này sẽ có entity_id như bên dưới
    payload = {"entity_id": "button.phong_ngu_esp32_s3_hanh_dong_vay_tay_chao"}
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"Calling HA API: {url} with entity_id: {payload['entity_id']}")
            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
            print(f"HA Response: {response.status_code} - {response.text}")
            if response.status_code in [200, 201]:
                return "Đã vẫy tay chào thành công."
            return f"Lỗi HA: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Lỗi kết nối tới HA: {str(e)}"
