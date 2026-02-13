import redis.asyncio as redis
from app.core.config import settings

token_blocklist = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(name=jti, value="", ex=settings.JWT_EXPIRY)


async def token_in_blocklist(jti:str) -> bool:
   jti =  await token_blocklist.get(jti)

   return jti is not None