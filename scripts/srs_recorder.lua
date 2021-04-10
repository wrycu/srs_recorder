local SRS_RECORDER = {}

SRS_RECORDER.SEND_PORT = 5190
-- this should be the IP address where the SRS recorder script is running
SRS_RECORDER.SEND_IP = '127.0.0.1'
SRS_RECORDER.SLOTTED = false

SRS_RECORDER.logFile = io.open(
    lfs.writedir()..[[Logs\srs_recorder.log]], "w"
)
function SRS_RECORDER.log(str)
    if SRS_RECORDER.logFile then
        SRS_RECORDER.logFile:write(os.date() .. " | " .. str .."\r\n")
        SRS_RECORDER.logFile.flush()
    end
end
SRS_RECORDER.log("SRS_RECORDER loading")
-- used to trigger recording once we load and to stop it once we're done
local socket = require("socket")
SRS_RECORDER.UDPSendSocket = socket.udp()
SRS_RECORDER.log("SRS_RECORDER loaded")

LuaExportStop = function()
    SRS_RECORDER.log("SRS_RECORDER MISSION STOPPED")
    socket.try(SRS_RECORDER.UDPSendSocket:sendto("MISSION_END", SRS_RECORDER.SEND_IP, SRS_RECORDER.SEND_PORT))
end

function LuaExportActivityNextEvent(t)
	local tNext = t
    tNext = tNext + 0.1
    local _data = LoGetSelfData()
    if (_data ~= nil and SRS_RECORDER.SLOTTED == false) then
        if LoGetModelTime() > 0 then
            SRS_RECORDER.log("SRS_RECORDER CAUGHT SLOT")
            socket.try(SRS_RECORDER.UDPSendSocket:sendto("MISSION_START", SRS_RECORDER.SEND_IP, SRS_RECORDER.SEND_PORT))
            SRS_RECORDER.SLOTTED = true
        else
            return tNext
        end
    end
end

SRS_RECORDER.log("SRS_RECORDER completed loading")
