from json import JSONDecodeError
from flask import request, Response
from flask_restful import Resource
from model.device_model import DeviceModel


class DeviceResource(Resource):

    def __init__(self, **kwargs):
        self.dataManager = kwargs['data_manager']

    def get(self, device_id):
        if device_id in self.dataManager.device_dictionary:
            return self.dataManager.device_dictionary[device_id].__dict__, 200
        else:
            return {'error': "Device Not Found !"}, 404

    def put(self, device_id):
        try:
            if device_id in self.dataManager.device_dictionary:
                # The boolean flag force the parsing of POST data as JSON irrespective of the mimetype
                json_data = request.get_json(force=True)
                deviceModel = DeviceModel(**json_data)
                if deviceModel.uuid != device_id:
                    return {'error': "UUID mismatch between body and resource"}, 400
                else:
                    self.dataManager.update_device(deviceModel)
                    return Response(status=204)
            else:
                return {'error': "Device UUID not found"}, 404
        except JSONDecodeError:
            return {'error': "Invalid JSON ! Check the request"}, 400
        except Exception as e:
            return {'error': "Generic Internal Server Error ! Reason: " + str(e)}, 500

    def delete(self, device_id):
        try:
            if device_id in self.dataManager.device_dictionary:
               self.dataManager.remove_device(device_id)
               return Response(status=204)
            else:
                return {'error': "Device UUID not found"}, 404
        except Exception as e:
            return {'error': "Generic Internal Server Error ! Reason: " + str(e)}, 500