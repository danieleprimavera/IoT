from json import JSONDecodeError
from flask import request, Response
from flask_restful import Resource, reqparse
from model.device_model import DeviceModel

class DevicesResource(Resource):

    def __init__(self, **kwargs):
        self.dataManager = kwargs['data_manager']

    def get(self):
        device_list = []
        for device in self.dataManager.device_dictionary.values():
            device_list.append(device.__dict__)
        return device_list, 200

    def post(self):
        try:
            json_data = request.get_json(force=True)
            deviceModel = DeviceModel(**json_data)
            if deviceModel.uuid in self.dataManager.device_dictionary:
                return {'error': "Device UUID already exists"}, 409
            else:
                self.dataManager.add_device(deviceModel)
                return Response(status=201, headers={
                    "Location": request.url + "/" + deviceModel.uuid})
        except JSONDecodeError:
            return {'error': "Invalid JSON ! Check the request"}, 400
        except Exception as e:
            return {'error': "Generic Internal Server Error ! Reason: " + str(e)}, 500
