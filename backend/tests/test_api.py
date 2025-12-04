import pytest
from httpx import AsyncClient,ASGITransport
from backend.api import app
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.mark.asyncio
async def test_check_free():
    async with AsyncClient(
        transport=ASGITransport(app = app),
        base_url="http://test"
    ) as ac:
        head = {
            "X-API-KEY":os.getenv("API")
        }
        response = await ac.get("/check/free/user1223",headers=head)
        assert response.status_code == 200 


