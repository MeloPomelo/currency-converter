import aiohttp
import yaml
import json
import trafaret as t
import redis.asyncio as redis
import xml.etree.ElementTree as ET


CONFIG_TRAFARET = t.Dict(
    {
        t.Key('redis'): t.Dict(
            {
                'port': t.Int(),
                'host': t.String(),
                'db': t.Int(),
                'minsize': t.Int(),
                'maxsize': t.Int(),
            }
        ),
        'host': t.String(),
        'port': t.Int(),
    }
)


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.safe_load(f)
    return CONFIG_TRAFARET.check(data)


async def init_redis(conf):
    redis_pool = redis.ConnectionPool(host=conf['host'], port=conf['port'], db=0)
    return redis.Redis(connection_pool=redis_pool)


async def close_redis(app):
    redis = app['redis']
    redis.connection_pool.disconnect()


async def get_currency_rates():
    async with aiohttp.ClientSession() as session:
            async with session.get('https://www.cbr.ru/scripts/XML_daily.asp') as resp:
                xml_text = await resp.text()
                root = ET.fromstring(xml_text)

                yield ("currency:RUB", 1)

                for valute in root.findall('Valute'):
                    char_code = valute.find('CharCode').text
                    rate = valute.find('Value').text.replace(',', '.')
                    nominal = valute.find('Nominal').text.replace(',', '.')

                    key = f"currency:{char_code}"
                    value = float(rate) / float(nominal)
            

                    yield (key, value)


def convert(from_value, to_value, amount):
    from_value = float(from_value)
    to_value = float(to_value)
    
    return amount * from_value / to_value


def create_json_response(status, data):
    return aiohttp.web.json_response(status=status, text=json.dumps(data))


def create_error_response(status, message):
    return create_json_response(status, {"message": message})

