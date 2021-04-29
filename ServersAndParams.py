static_api_server = "https://static-maps.yandex.ru/1.x/"
geocode_api_server = "https://geocode-maps.yandex.ru/1.x/"
places_api_server = "https://search-maps.yandex.ru/v1/"
static_params = {
    "l": "map",
}
geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "format": "json",
    "results": 1
}
places_params = {
    "lang": "ru_RU",
    "apikey": "575a0baa-461e-472c-8be2-bb4234d97a53",
    "results": 1
}
format_keys = {"geocode": "geocode", "геокод": "geocode", "l": "l", "layer": "l", "слой": "l", "z": "z", "zoom": "z",
               "масштаб": "z", "scale": "scale", "увеличение": "scale", "pt": "pt", "marker": "pt", "метка": "pt",
               "kind": "kind", "toponym": "kind", "топоним": "kind", "text": "text", "place": "text", "место": "text",
               "results": "results", "результаты": "results", "trf": "trf", "traffic": "trf", "траффик": "trf"
               }
format_values = {"sat": "sat", "satellite": "sat", "спутник": "sat", "map": "map", "схема": "map", "sat,skl": "sat,skl",
                 "sat,map": "sat,skl", "hybrid": "sat,skl", "гибрид": "sat,skl", "map,trf": "map,trf",
                 "sat,trf": "sat,trf", "sat,skl,trf": "sat,skl,trf", "house": "house", "дом": "house",
                 "street": "street", "улица": "street", "metro": "metro", "метро": "metro", "district": "district",
                 "район": "district", "locality": "locality", "пункт": "locality"
                 }
