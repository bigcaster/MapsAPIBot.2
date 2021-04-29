import requests
from serversAndParams import static_api_server, geocode_api_server, places_api_server, format_keys, format_values
import copy


class MapAPI:
    def __init__(self):
        self.message = None
        self.message_params = {}
        self.kind_param = None
        self.static_params = {}
        self.geocoder_params = {}
        self.places_params = {}

    def main(self, message):
        self.reset_params()
        self.message = message.lower().split(';')
        self.message_params = {}

        for param in self.message:
            if '=' in param:
                param_list = list((map(str.strip, param.split('='))))
                if len(param_list) != 2:
                    return "Ошибка инициализации параметра"
                key, value = param_list
                if key in format_keys:
                    right_key = format_keys[key]
                    if right_key in self.message_params:
                        return "Одинаковые параметры в запросе"
                    self.message_params[right_key] = value

        geocode_param = "geocode" in self.message_params
        text_param = "text" in self.message_params
        self.kind_param = "kind" in self.message_params
        if not geocode_param and not text_param:
            return 'Отсутствует обязательный параметр ("geocode" или "text")'
        elif geocode_param and text_param:
            return 'Параметры "geocode" и "text" в одном запросе'
        elif text_param and self.kind_param:
            return 'Параметры "text" и "kind" в одном запросе'

        for key, value in self.message_params.items():
            if key in ["l", "z", "scale", "pt", "trf"]:
                if key == "l":
                    if value in format_values:
                        value = format_values[value]
                    else:
                        return 'Недопустимый аргумент в параметре "l"'
                elif key == "z" and not (value.isdigit() and 0 <= int(value) <= 17):
                    return 'Недопустимый аргумент в параметре "z"'
                elif key == "scale" and not (value.isdigit() and 1 <= float(value) <= 4):
                    return 'Недопустимый аргумент в параметре "scale"'
                self.static_params[key] = value

        if geocode_param:
            output = self.geocode_request()
        else:
            output = self.text_request()
        if isinstance(output, str):
            return output
        static_response = requests.get(static_api_server, params=self.static_params)
        if not static_response:
            return f"""Ошибка в запросе: {static_api_server}
Http статус: {static_response.status_code} ({static_response.reason})"""

        self.make_image(static_response.content)
        return output

    def geocode_request(self):
        for key, value in self.message_params.items():
            if key in ["geocode", "kind", "results"]:
                if key == "kind":
                    if value in format_values:
                        value = format_values[value]
                    else:
                        return 'Недопустимый аргумент в параметре "kind"'
                self.geocoder_params[key] = value

        geocode_response = requests.get(geocode_api_server, params=self.geocoder_params)
        if not geocode_response:
            return f"""Ошибка запроса: {geocode_api_server}
Http статус: {geocode_response.status_code} ({geocode_response.reason})"""
        json_geocode_response = geocode_response.json()
        pos = None
        try:
            objects = []
            members = json_geocode_response["response"]["GeoObjectCollection"]["featureMember"]
            if self.kind_param:
                members = [members[0]]
            for member in members:
                name = member["GeoObject"]["name"]
                envelope = member["GeoObject"]["boundedBy"]["Envelope"]
                lower_lon, lower_lat = map(float, envelope["lowerCorner"].split())
                upper_lon, upper_lat = map(float, envelope["upperCorner"].split())
                spn = f"{upper_lon - lower_lon},{upper_lat - lower_lat}"
                pos = ", ".join(member["GeoObject"]["Point"]["pos"].split())
                address = member["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
                if not self.kind_param:
                    info = {"Название": name, "Адрес": address, "Координаты": pos, "spn": spn}
                    objects.append(info)
        except Exception:
            return "Произошла ошибка во время поиска объектов"
        if not objects and not self.kind_param:
            return "Не удалось найти объекты по вашему запросу"
        init_marker_params_output = self.init_marker_params()
        if len(init_marker_params_output) == 1:
            return init_marker_params_output
        marker_color, marker_size = init_marker_params_output
        if self.kind_param:
            find_toponyms_output = self.find_toponyms(pos)
            if isinstance(find_toponyms_output, str):
                return find_toponyms_output
            toponyms = find_toponyms_output
            self.static_params["pt"] = '~'.join(
                [f"{','.join(toponym['Координаты'].split(', '))},pm2{marker_color}{marker_size}" for toponym in
                 toponyms])
            if "z" not in self.static_params:
                self.static_params["spn"] = max(toponym["spn"] for toponym in toponyms)
            return toponyms
        else:
            self.static_params["pt"] = '~'.join(
                [f"{','.join(geo_object['Координаты'].split(', '))},pm2{marker_color}{marker_size}" for geo_object
                 in objects])
            if "z" not in self.static_params:
                self.static_params["spn"] = max(geo_object["spn"] for geo_object in objects)
            return objects

    def text_request(self):
        for key, value in self.message_params.items():
            if key in ["text", "results"]:
                self.places_params[key] = value
        places_response = requests.get(places_api_server, params=self.places_params)
        if not places_response:
            return f"""Ошибка в запросе: {places_api_server}
Http статус: {places_response.status_code} ({places_response.reason})"""

        json_places_response = places_response.json()
        features = []
        try:
            for feature in json_places_response["features"]:
                info = {"Название": feature.get("properties", {"name": "Не найдено"}).get("name", "Не найдено"),
                        "Адрес": feature.get("properties", {"description": "Не найдено"}).get("description",
                                                                                              "Не найдено")}
                coords = feature.get("geometry", {"coordinates": "Не найдено"}).get("coordinates", "Не найдено")
                if coords != 'Не найдено':
                    coords = ', '.join(map(str, coords))
                info["Координаты"] = coords
                spn = feature.get("properties", {"boundedBy": None}).get("boundedBy", None)
                if spn is not None:
                    lower, upper = spn
                    spn = f"{upper[0] - lower[0]},{upper[1] - lower[1]}"
                info["spn"] = spn
                if "CompanyMetaData" in feature["properties"]:
                    meta_data = feature.get("properties", {"CompanyMetaData": "Не найдено"}).get("CompanyMetaData",
                                                                                                 "Не найдено")
                    if meta_data == "Не найдено":
                        info["Категория"] = info["Время работы"] = info["Сайт"] = info["Номера"] = "Не найден"
                        features.append(info)
                        continue
                    info["Категория"] = " / ".join(
                        [category["name"] for category in meta_data.get("Categories", [{"name": "Не найдено"}])])
                    info["Время работы"] = meta_data.get("Hours", {'text': "Не найдено"}).get("text", "Не найдено")
                    info["Сайт"] = meta_data.get("url", "Не найдено")
                    if "Phones" in meta_data:
                        info["Номера"] = " / ".join(
                            [phone["formatted"] for phone in meta_data.get("Phones", ["Не найдено"])])
                else:
                    info["Адрес"] = feature.get("properties", {"description": "Не найдено"}).get("description",
                                                                                                 "Не найден")
                features.append(info)
        except Exception:
            return "Произошла ошибка во время поиска организаций"
        if not features:
            return "Не удалось найти организации по вашему запросу"
        init_marker_params_output = self.init_marker_params()
        if isinstance(init_marker_params_output, str):
            return init_marker_params_output
        marker_color, marker_size = init_marker_params_output
        self.static_params["pt"] = "~".join(
            f"{','.join(feature['Координаты'].split(', '))},pm2{marker_color}{marker_size}" for feature in features)
        if "z" not in self.static_params:
            self.static_params["spn"] = max(info["spn"] for info in features)
        return features

    def reset_params(self):
        from serversAndParams import static_params, geocoder_params, places_params
        self.static_params = copy.deepcopy(static_params)
        self.geocoder_params = copy.deepcopy(geocoder_params)
        self.places_params = copy.deepcopy(places_params)

    def find_toponyms(self, pos):
        self.geocoder_params["geocode"] = pos
        toponym_geocode_response = requests.get(geocode_api_server, params=self.geocoder_params)
        json_toponym_geocode_response = toponym_geocode_response.json()
        try:
            toponyms = []
            for member in json_toponym_geocode_response["response"]["GeoObjectCollection"]["featureMember"]:
                envelope = member["GeoObject"]["boundedBy"]["Envelope"]
                l1, l2 = map(float, envelope["lowerCorner"].split())
                u1, u2 = map(float, envelope["upperCorner"].split())
                spn = f"{u1 - l1},{u2 - l2}"
                info = {"Название": member["GeoObject"]["name"],
                        "Координаты": ", ".join(member["GeoObject"]["Point"]["pos"].split()),
                        "Адрес": member["GeoObject"]["description"], "spn": spn}
                toponyms.append(info)
        except Exception:
            return "Произошла ошибка во время поиска топонимов"
        if not toponyms:
            return "Не удалось найти топонимы по вашему запросу"
        return toponyms

    def init_marker_params(self):
        marker_definition = self.message_params.get("pt", "nt,m").split(',')
        if len(marker_definition) != 2:
            return "Неверное количество аргументов в параметре метки"
        marker_color, marker_size = marker_definition
        if marker_color not in ["wt", "do", "db", "bl", "gn", "dg", "gr", "lb", "nt", "or", "pn", "rd", "vv", "yw",
                                "org", "dir", "bylw"] or marker_size not in ["m", "l"]:
            return "Недопустимое значение аргументов в параметре метки"
        return marker_color, marker_size

    def make_image(self, content):
        map_file = "map.png"
        with open(map_file, 'wb') as file:
            file.write(content)
