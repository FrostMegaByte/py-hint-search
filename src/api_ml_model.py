import json
from typing import Any, Dict, List
import requests
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Type4PyException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TypeT5Exception(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def get_ordered_type4py_predictions(python_code: str) -> List[Dict[str, Any]]:
    # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
    response = requests.post("http://localhost:5001/api/predict?tc=0", python_code)
    json_response = response.json()

    if json_response["error"] is not None:
        raise Type4PyException(json_response["error"])

    functions_predictions = {}
    for class_obj in json_response["response"]["classes"]:
        for func in class_obj["funcs"]:
            location_index = func["fn_lc"][0][0]
            functions_predictions[location_index] = func

    for func in json_response["response"]["funcs"]:
        location_index = func["fn_lc"][0][0]
        functions_predictions[location_index] = func

    functions_predictions = dict(sorted(functions_predictions.items()))
    functions_predictions = functions_predictions.values()

    filter_fields = ["q_name", "params_p", "ret_type_p"]
    type_predictions = list(
        map(
            lambda f: {key: f[key] for key in f if key in filter_fields},
            functions_predictions,
        )
    )
    return type_predictions


def get_typet5_predictions() -> List[Dict[str, Any]]:
    response = requests.get("http://localhost:5000/api")
    json_response = response.json()

    if json_response["error"] is not None:
        raise TypeT5Exception(json_response["error"])

    type_predictions_per_file = {}
    for file_response in json_response["responses"]:
        functions_predictions = []
        for class_obj in file_response["response"]["classes"]:
            functions_predictions += class_obj["funcs"]

        functions_predictions += file_response["response"]["funcs"]

        filter_fields = ["q_name", "params_p", "ret_type_p"]
        type_predictions = list(
            map(
                lambda f: {key: f[key] for key in f if key in filter_fields},
                functions_predictions,
            )
        )
        type_predictions_per_file[file_response["file_path"]] = type_predictions
    return type_predictions_per_file
