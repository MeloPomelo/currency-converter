from aiohttp_apispec import docs, response_schema, querystring_schema, json_schema

from app.utils import convert, get_currency_rates, create_json_response, create_error_response
from app.schemas import (
    ConvertResponseSchema,
    ConvertRequestSchema, 
    CurrenciesSchema,
    ImportParamsSchema,
    ImportResponseSchema,
)


class SiteHandler:
    def __init__(self, redis):
        self.redis = redis


    @docs(
        tags=["main"],
        summary="Converts currency",
        description="Converts the specified amount of tre one currency to another",
        responses={
            404: {"description": "Not found"}, 
            422: {"description": "Validation error"},
        },
    )
    @querystring_schema(ConvertRequestSchema)
    @response_schema(ConvertResponseSchema)
    async def convert_currencies(self, request):
        params = request["querystring"]

        from_currency = params["from_currency"].upper()
        to_currency = params["to_currency"].upper()

        amount = float(params["amount"])

        from_key = f"currency:{from_currency}"
        to_key = f"currency:{to_currency}"
        
        from_value = await self.redis.get(from_key)
        to_value = await self.redis.get(to_key)
        
        if not from_value:
            return create_error_response(404, f"{from_currency} not found")

        if not to_value:
            return create_error_response(404, f"{to_currency} not found")
        
        result = {
            "from": from_currency,
            "to": to_currency,
            "amount": amount,
            "result": convert(from_value, to_value, amount)
        }
        
        return create_json_response(200, result)
    

    @docs(
        tags=["main"],
        summary="Set currency data manually",
        description="The method is used to set data on the exchange rates of the Russian ruble (RUB) for various currencies. \
                    If `merge` is set to 0, the old data is invalidated. If `merge` is set to 1, the new \
                    data will overwrite the old data, but the old data remains relevant if not erased. \
                    Currency code should adhere to the ISO 4217 standard",
        responses={
            422: {"description": "Validation error"},
        },
    )
    @querystring_schema(ImportParamsSchema)
    @json_schema(CurrenciesSchema)
    @response_schema(ImportResponseSchema)
    async def add_currencies_rates(self, request):
        merge = int(request["querystring"]["merge"])
        currencies = request["json"]["currencies"]

        if merge == 0:
            keys = await self.redis.keys("currency:*")
            if keys:
                await self.redis.delete(*keys)
        
        for currency in currencies:
            key = f"currency:{currency['char_code'].upper()}"
            value = currency["value"]
            await self.redis.set(key, value)

        await self.redis.set("currency:RUB", 1)

        return create_json_response(201, currencies)


    @docs(
        tags=["extra"],
        summary="Get all currencies from data base",
        responses={
            404: {"description": "No currencies found"},
        },
    )
    @response_schema(CurrenciesSchema)
    async def get_currencies(self, request):
        keys = await self.redis.keys("currency:*")
        if not keys:
            return create_error_response(404, "No currencies found")
        
        currencies = []
        for key in keys:
            currency = {}
            char_code = key.decode("utf-8").split(":")[-1]
            value = await self.redis.get(key)
            currency['char_code'] = char_code
            currency['value'] = float(value)
            currencies.append(currency)
        
        return create_json_response(200, {'currencies': currencies})


    @docs(
        tags=["extra"],
        summary="Set the currency data automatically",
        description="Provides data on the exchange rates of the Russian ruble (RUB) for 33 different currencies from the website of the Central Bank of the Russian Federation",
        responses={
            201: {"description": "Data successfully updated"},
            502: {"description": "Unsuccessful request to the Central Bank's website"},
        },
    )
    async def get_currency_rates_from_cb(self, request):
        try:
            async for currency in get_currency_rates():
                await self.redis.set(currency[0], currency[1])      
            return create_json_response(201, {"message": "Data successfully updated"})
        except:
            return create_error_response(502, {"message": "Unsuccessful request to the Central Bank's website"})
        
   


