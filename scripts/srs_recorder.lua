local SRS_RECORDER = {}

SRS_RECORDER.SEND_PORT = 5190
-- this should be the IP address where the SRS recorder script is running
SRS_RECORDER.SEND_IP = '127.0.0.1'

SRS_RECORDER.logFile = io.open(
    lfs.writedir()..[[Logs\srs_recorder.log]], "w"
)
function SRS_RECORDER.log(str)
    if SRS_RECORDER.logFile then
        SRS_RECORDER.logFile:write(str.."\n")
        SRS_RECORDER.logFile.flush()
    end
end

SRS_RECORDER.log("SRS_RECORDER starting loading")

--load sockets so we can communicate with liberation
package.path = package.path..";.\\LuaSocket\\?.lua;"
package.cpath = package.cpath..";.\\LuaSocket\\?.dll;"
package.path =
      package.path..";"
    .. './MissionEditor/?.lua;'
    .. './MissionEditor/themes/main/?.lua;'
    .. './MissionEditor/modules/?.lua;'
    .. './Scripts/?.lua;'
    .. './LuaSocket/?.lua;'
    .. './Scripts/UI/?.lua;'
    .. './Scripts/UI/Multiplayer/?.lua;'
    .. './Scripts/DemoScenes/?.lua;'

SRS_RECORDER.log("SRS_RECORDER included imports")

local socket = require("socket")

function script_path()
   local str = debug.getinfo(2, "S").source:sub(1)
   return str:match("(.*/)")
end

-- used to trigger recording once we load and to stop it once we're done
SRS_RECORDER.UDPSendSocket = socket.udp()

LuaExportStop = function()
    SRS_RECORDER.log("SRS_RECORDER MISSION STOPPED")
    socket.try(SRS_RECORDER.UDPSendSocket:sendto("MISSION_END", SRS_RECORDER.SEND_IP, SRS_RECORDER.SEND_PORT))
end

function LuaExportActivityNextEvent(t)
	local tNext = t
    tNext = tNext + 0.1
    local _data = LoGetSelfData()
    if _data ~= nil then
        SRS_RECORDER.log(LoGetModelTime())
        if LoGetModelTime() > 0 then
            SRS_RECORDER.log("SRS_RECORDER CAUGHT SLOT")
            socket.try(SRS_RECORDER.UDPSendSocket:sendto("MISSION_START", SRS_RECORDER.SEND_IP, SRS_RECORDER.SEND_PORT))
        else
            return tNext
        end
    end
end

SRS_RECORDER.log("SRS_RECORDER completed loading")
