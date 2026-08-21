import httpx
from app.core.config import settings

async def play_audio_on_ha(media_url: str, entity_id: str = "media_player.loa_esp32"):
    """
    Gửi yêu cầu tới Home Assistant để phát một file audio (media_url) lên loa.
    """
    if not settings.HA_URL or not settings.HA_TOKEN:
        print("Chưa cấu hình HA_URL hoặc HA_TOKEN, bỏ qua phát âm thanh.")
        return False
        
    url = f"{settings.HA_URL.rstrip('/')}/api/services/media_player/play_media"
    headers = {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "entity_id": entity_id,
        "media_content_id": media_url,
        "media_content_type": "music"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"Lỗi HA play_media: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Lỗi kết nối tới HA: {str(e)}")
        return False
