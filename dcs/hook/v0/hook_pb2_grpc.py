# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from dcs.hook.v0 import hook_pb2 as dcs_dot_hook_dot_v0_dot_hook__pb2


class HookServiceStub(object):
    """APis that are part of the hook environment
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetMissionName = channel.unary_unary(
                '/dcs.hook.v0.HookService/GetMissionName',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionNameRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionNameResponse.FromString,
                )
        self.GetMissionFilename = channel.unary_unary(
                '/dcs.hook.v0.HookService/GetMissionFilename',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionFilenameRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionFilenameResponse.FromString,
                )
        self.GetMissionDescription = channel.unary_unary(
                '/dcs.hook.v0.HookService/GetMissionDescription',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionDescriptionRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionDescriptionResponse.FromString,
                )
        self.GetPaused = channel.unary_unary(
                '/dcs.hook.v0.HookService/GetPaused',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetPausedRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetPausedResponse.FromString,
                )
        self.SetPaused = channel.unary_unary(
                '/dcs.hook.v0.HookService/SetPaused',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.SetPausedRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.SetPausedResponse.FromString,
                )
        self.StopMission = channel.unary_unary(
                '/dcs.hook.v0.HookService/StopMission',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.StopMissionRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.StopMissionResponse.FromString,
                )
        self.ReloadCurrentMission = channel.unary_unary(
                '/dcs.hook.v0.HookService/ReloadCurrentMission',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ReloadCurrentMissionRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ReloadCurrentMissionResponse.FromString,
                )
        self.LoadNextMission = channel.unary_unary(
                '/dcs.hook.v0.HookService/LoadNextMission',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadNextMissionRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadNextMissionResponse.FromString,
                )
        self.LoadMission = channel.unary_unary(
                '/dcs.hook.v0.HookService/LoadMission',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadMissionRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadMissionResponse.FromString,
                )
        self.Eval = channel.unary_unary(
                '/dcs.hook.v0.HookService/Eval',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.EvalRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.EvalResponse.FromString,
                )
        self.ExitProcess = channel.unary_unary(
                '/dcs.hook.v0.HookService/ExitProcess',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ExitProcessRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ExitProcessResponse.FromString,
                )
        self.IsMultiplayer = channel.unary_unary(
                '/dcs.hook.v0.HookService/IsMultiplayer',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsMultiplayerRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsMultiplayerResponse.FromString,
                )
        self.IsServer = channel.unary_unary(
                '/dcs.hook.v0.HookService/IsServer',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsServerRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsServerResponse.FromString,
                )
        self.BanPlayer = channel.unary_unary(
                '/dcs.hook.v0.HookService/BanPlayer',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.BanPlayerRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.BanPlayerResponse.FromString,
                )
        self.UnbanPlayer = channel.unary_unary(
                '/dcs.hook.v0.HookService/UnbanPlayer',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.UnbanPlayerRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.UnbanPlayerResponse.FromString,
                )
        self.GetBannedPlayers = channel.unary_unary(
                '/dcs.hook.v0.HookService/GetBannedPlayers',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetBannedPlayersRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetBannedPlayersResponse.FromString,
                )
        self.GetUnitType = channel.unary_unary(
                '/dcs.hook.v0.HookService/GetUnitType',
                request_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetUnitTypeRequest.SerializeToString,
                response_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetUnitTypeResponse.FromString,
                )


class HookServiceServicer(object):
    """APis that are part of the hook environment
    """

    def GetMissionName(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_getMissionName
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetMissionFilename(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_getMissionFilename
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetMissionDescription(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_getMissionDescription
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPaused(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_getPause
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetPaused(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_setPause
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StopMission(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_stopMission
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReloadCurrentMission(self, request, context):
        """Reload the currently running mission
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def LoadNextMission(self, request, context):
        """Load the next mission in the server mission list. Note that it does
        not loop back to the first mission once the end of the mission list
        has been reached
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def LoadMission(self, request, context):
        """Load a specific mission file. This does not need to be in the mission
        list.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Eval(self, request, context):
        """Evaluate some Lua inside of the hook environment and return the result as a
        JSON string. Disabled by default.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ExitProcess(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_exitProcess
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def IsMultiplayer(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_isMultiplayer
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def IsServer(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_isServer
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BanPlayer(self, request, context):
        """Bans a player that is currently connected to the server
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UnbanPlayer(self, request, context):
        """Unbans a player via their globally unique ID
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetBannedPlayers(self, request, context):
        """Get a list of all the banned players
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetUnitType(self, request, context):
        """https://wiki.hoggitworld.com/view/DCS_func_getUnitType
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_HookServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetMissionName': grpc.unary_unary_rpc_method_handler(
                    servicer.GetMissionName,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionNameRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionNameResponse.SerializeToString,
            ),
            'GetMissionFilename': grpc.unary_unary_rpc_method_handler(
                    servicer.GetMissionFilename,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionFilenameRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionFilenameResponse.SerializeToString,
            ),
            'GetMissionDescription': grpc.unary_unary_rpc_method_handler(
                    servicer.GetMissionDescription,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionDescriptionRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionDescriptionResponse.SerializeToString,
            ),
            'GetPaused': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPaused,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetPausedRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetPausedResponse.SerializeToString,
            ),
            'SetPaused': grpc.unary_unary_rpc_method_handler(
                    servicer.SetPaused,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.SetPausedRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.SetPausedResponse.SerializeToString,
            ),
            'StopMission': grpc.unary_unary_rpc_method_handler(
                    servicer.StopMission,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.StopMissionRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.StopMissionResponse.SerializeToString,
            ),
            'ReloadCurrentMission': grpc.unary_unary_rpc_method_handler(
                    servicer.ReloadCurrentMission,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ReloadCurrentMissionRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ReloadCurrentMissionResponse.SerializeToString,
            ),
            'LoadNextMission': grpc.unary_unary_rpc_method_handler(
                    servicer.LoadNextMission,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadNextMissionRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadNextMissionResponse.SerializeToString,
            ),
            'LoadMission': grpc.unary_unary_rpc_method_handler(
                    servicer.LoadMission,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadMissionRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.LoadMissionResponse.SerializeToString,
            ),
            'Eval': grpc.unary_unary_rpc_method_handler(
                    servicer.Eval,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.EvalRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.EvalResponse.SerializeToString,
            ),
            'ExitProcess': grpc.unary_unary_rpc_method_handler(
                    servicer.ExitProcess,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ExitProcessRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.ExitProcessResponse.SerializeToString,
            ),
            'IsMultiplayer': grpc.unary_unary_rpc_method_handler(
                    servicer.IsMultiplayer,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsMultiplayerRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsMultiplayerResponse.SerializeToString,
            ),
            'IsServer': grpc.unary_unary_rpc_method_handler(
                    servicer.IsServer,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsServerRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.IsServerResponse.SerializeToString,
            ),
            'BanPlayer': grpc.unary_unary_rpc_method_handler(
                    servicer.BanPlayer,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.BanPlayerRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.BanPlayerResponse.SerializeToString,
            ),
            'UnbanPlayer': grpc.unary_unary_rpc_method_handler(
                    servicer.UnbanPlayer,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.UnbanPlayerRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.UnbanPlayerResponse.SerializeToString,
            ),
            'GetBannedPlayers': grpc.unary_unary_rpc_method_handler(
                    servicer.GetBannedPlayers,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetBannedPlayersRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetBannedPlayersResponse.SerializeToString,
            ),
            'GetUnitType': grpc.unary_unary_rpc_method_handler(
                    servicer.GetUnitType,
                    request_deserializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetUnitTypeRequest.FromString,
                    response_serializer=dcs_dot_hook_dot_v0_dot_hook__pb2.GetUnitTypeResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dcs.hook.v0.HookService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class HookService(object):
    """APis that are part of the hook environment
    """

    @staticmethod
    def GetMissionName(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/GetMissionName',
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionNameRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionNameResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetMissionFilename(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/GetMissionFilename',
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionFilenameRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionFilenameResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetMissionDescription(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/GetMissionDescription',
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionDescriptionRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetMissionDescriptionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetPaused(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/GetPaused',
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetPausedRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetPausedResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetPaused(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/SetPaused',
            dcs_dot_hook_dot_v0_dot_hook__pb2.SetPausedRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.SetPausedResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StopMission(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/StopMission',
            dcs_dot_hook_dot_v0_dot_hook__pb2.StopMissionRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.StopMissionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ReloadCurrentMission(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/ReloadCurrentMission',
            dcs_dot_hook_dot_v0_dot_hook__pb2.ReloadCurrentMissionRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.ReloadCurrentMissionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def LoadNextMission(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/LoadNextMission',
            dcs_dot_hook_dot_v0_dot_hook__pb2.LoadNextMissionRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.LoadNextMissionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def LoadMission(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/LoadMission',
            dcs_dot_hook_dot_v0_dot_hook__pb2.LoadMissionRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.LoadMissionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Eval(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/Eval',
            dcs_dot_hook_dot_v0_dot_hook__pb2.EvalRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.EvalResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ExitProcess(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/ExitProcess',
            dcs_dot_hook_dot_v0_dot_hook__pb2.ExitProcessRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.ExitProcessResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def IsMultiplayer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/IsMultiplayer',
            dcs_dot_hook_dot_v0_dot_hook__pb2.IsMultiplayerRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.IsMultiplayerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def IsServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/IsServer',
            dcs_dot_hook_dot_v0_dot_hook__pb2.IsServerRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.IsServerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def BanPlayer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/BanPlayer',
            dcs_dot_hook_dot_v0_dot_hook__pb2.BanPlayerRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.BanPlayerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UnbanPlayer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/UnbanPlayer',
            dcs_dot_hook_dot_v0_dot_hook__pb2.UnbanPlayerRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.UnbanPlayerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetBannedPlayers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/GetBannedPlayers',
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetBannedPlayersRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetBannedPlayersResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetUnitType(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/dcs.hook.v0.HookService/GetUnitType',
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetUnitTypeRequest.SerializeToString,
            dcs_dot_hook_dot_v0_dot_hook__pb2.GetUnitTypeResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
