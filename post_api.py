import httpx
import asyncio

async def post_to_jarvis_api(text_input: str = "คุณชื่ออะไร") -> dict | None:
    url = "http://localhost:5678/webhook/c0342492-3ac5-42da-be4a-c6f06be38d6a"
    payload = {"text": text_input}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            try:
                return response.json()
            except ValueError:
                print("⚠️ ไม่สามารถแปลง response เป็น JSON ได้:", response.text)
                return None

        except httpx.RequestError as e:
            print(f"❌ Request failed: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unknown error: {e}")
            return None
