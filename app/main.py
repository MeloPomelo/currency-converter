import asyncio
import pathlib
import logging

from aiohttp import web
from aiohttp_apispec import setup_aiohttp_apispec, validation_middleware

from app.utils import load_config, init_redis, close_redis
from app.routes import setup_routes
from app.handlers import SiteHandler


BASE_DIR = pathlib.Path(__file__).parent.parent


async def setup_redis(app, conf):
    redis = await init_redis(conf['redis'])
    app["redis"] = redis
    return redis


async def create_app():
    conf = load_config(BASE_DIR / 'config' / 'config.yaml')

    app = web.Application(middlewares=[validation_middleware])
    redis = await setup_redis(app, conf)
    handler = SiteHandler(redis)
    app.on_cleanup.append(close_redis)
    setup_routes(app, handler)

    host, port = conf['host'], conf['port']

    setup_aiohttp_apispec(
        app=app,
        title='Currency Converter API',
        version='v1',
        url='/api/docs/swagger.json',
        swagger_path='/api/docs',
    )

    return app, host, port


def main():
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(create_app())
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()
