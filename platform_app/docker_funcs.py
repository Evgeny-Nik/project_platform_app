from app_config import logger, DOCKER_HUB_USERNAME, DOCKER_HUB_ACCESS_TOKEN
import asyncio
import aiohttp
from cache_config import get_docker_images_cache, update_docker_images_cache


async def fetch_image_tags(session, repo_name):
    headers = {
        'Authorization': f'Bearer {DOCKER_HUB_ACCESS_TOKEN}',
        'Accept': 'application/json'
    }
    # Ensure no newline or carriage return characters in the headers
    headers = {k: v.replace('\n', '').replace('\r', '') for k, v in headers.items()}

    url = f"https://hub.docker.com/v2/repositories/{DOCKER_HUB_USERNAME}/{repo_name}/tags/"

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            tags = [tag['name'] for tag in data.get('results', [])]
            return repo_name, tags
        else:
            logger.error(f"Failed to fetch tags for {repo_name}")
            return repo_name, []


async def fetch_images_and_tags():
    headers = {
        'Accept': 'application/json',
    }
    images_dict = {}
    url = f'https://hub.docker.com/v2/repositories/{DOCKER_HUB_USERNAME}/'

    async with aiohttp.ClientSession(headers=headers) as session:
        while url:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    repositories = data.get('results', [])
                    tasks = [fetch_image_tags(session, repo['name']) for repo in repositories]
                    results = await asyncio.gather(*tasks)
                    images_dict.update(dict(results))
                else:
                    logger.error("Unable to fetch images")
                url = data.get('next', None)

    return images_dict


async def update_docker_images_cache_async():
    while True:
        logger.debug("Starting image cache update...")
        docker_list = await fetch_images_and_tags()
        update_docker_images_cache(docker_list)
        logger.debug(f"Images cache updated: {get_docker_images_cache()}")
        # Update every 10 minutes (600 seconds)
        await asyncio.sleep(60)


# Function to run the async function in a separate thread
def update_docker_images_cache_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_docker_images_cache_async())
