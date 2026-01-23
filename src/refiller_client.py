from dataclasses import dataclass, field
import aiohttp


@dataclass
class RefillerClient:
    base_url: str
    client: aiohttp.ClientSession = field(
        default_factory=aiohttp.ClientSession, init=False
    )

    async def login(self, username: str, password: str, office: str) -> str:
        login_url = f"{self.base_url}/login"
        payload = {
            "office": office,
            "username": username,
            "password": password
        }

        async with self.client.post(
            login_url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            allow_redirects=False,
        ) as response:
            response.raise_for_status()
            cookie = response.headers.get("Set-Cookie")
            if not cookie:
                raise ValueError("Login failed: No session cookie received")
            return cookie

    async def request_refill(self, cookie: str, med: str) -> bool:
        refill_url = f"{self.base_url}/msgs/newmsg"
        payload = {
            "meds": med,
            "subject": "R",
            "reply": "",
            "type": "R",
            "msg": ""
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": cookie,
        }
        async with self.client.post(
            refill_url, data=payload, headers=headers
        ) as response:
            response.raise_for_status()
            return response.status == 200

    async def close(self):
        await self.client.close()
