def setup_routes(app, handler):
    router = app.router
    h = handler
    router.add_get('/convert', h.convert_currencies, allow_head=False)   
    router.add_get('/currencies', h.get_currencies, allow_head=False)   
    router.add_post('/database', h.add_currencies_rates)
    router.add_post('/databse_central_bank', h.get_currency_rates_from_cb)