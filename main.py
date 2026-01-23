import asyncio
import logging

from src.refiller_client import RefillerClient
from src.config import Config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("💊 Starting refiller service...")

    config = Config.from_toml()
    client = RefillerClient(config.base_url)

    try:
        logger.info("🔐 Logging in to retrieve session cookie...")
        cookie = await client.login(config.username, config.password, config.office)
        logger.info("🍪 Login successful, requesting medication refill...")
        success = await client.request_refill(cookie, config.med_id)
        if success:
            logger.info("✅ Medication refill request successful!")
        else:
            logger.error("❌ Medication refill request failed...")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
