from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import Int, Str, Float, Length, Nested
from marshmallow.validate import Length, Range


class ConvertRequestSchema(Schema):
    from_currency = Str(data_key="from", validate=Length(equal=3), required=True, description="The currency code of the amount to be converted from (ISO 4217)")
    to_currency = Str(data_key="to", validate=Length(equal=3), required=True, description="The currency code to convert the amount to (ISO 4217)")
    amount = Float(required=True, description="The amount to be converted")

    @validates('amount')
    def validate_amount(self, value: float):
        if value <= 0:
            raise ValidationError("Can't be negative")


class ConvertResponseSchema(ConvertRequestSchema):
    result = Float(description="The converted amount in the target currency")


class CurrencySchema(Schema):
    char_code = Str(validate=Length(equal=3), required=True, description="The currency code (ISO 4217)")
    value = Float(required=True, description="The value of the currency")

    @validates('char_code')
    def validate_char_code(self, value: float):
        if value.upper() == "RUB":
            raise ValidationError("RUB already in the database and always equal to 1")

    @validates('value')
    def validate_value(self, value: float):
        if value <= 0:
            raise ValidationError("Can't be negative")


class CurrenciesSchema(Schema):
    currencies = Nested(CurrencySchema, many=True, required=True, validate=Length(max=200))

    @validates_schema
    def validate_unique_char_code(self, data, **_):
        char_codes = set()
        for currency in data['currencies']:
            if currency['char_code'].upper() in char_codes:
                raise ValidationError(
                    f"CharCode {currency['char_code']} is not unique"
                )
            char_codes.add(currency['char_code'].upper())



class ImportParamsSchema(Schema):
     merge = Int(validate=Range(min=0, max=1), required=True, description="Specifies the merging behavior for adding new currency data")



class ImportResponseSchema(ImportParamsSchema, CurrenciesSchema):
    pass
