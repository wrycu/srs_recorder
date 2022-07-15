-- require a recent version of Tacview
local Tacview = require("Tacview188")

-- Configure addon details before we can mess anything up
Tacview.AddOns.Current.SetTitle("SRS Recorder")
Tacview.AddOns.Current.SetVersion("1.0.0")
Tacview.AddOns.Current.SetAuthor("Wrycu")
Tacview.AddOns.Current.SetNotes("Automatically loads SRS recordings")

-- listen for file load events and attempt to load matching recordings
function handle_file_load(fileNames)
    Tacview.Log.Info("caught file load")
    Tacview.Log.Info(fileNames)
    -- parse out the mission name and date it was run
    msn_name, date = parse_file_name(fileNames)
    Tacview.Log.Info("found msn " .. msn_name .. " from " .. date)
    -- check to see if we have any matching SRS recordings
    matching_audio = find_audio(msn_name, date, Tacview.Path.GetDirectoryName(fileNames))
    -- attempt to load the recordings
    load_audio(matching_audio)
end

-- extract the MSN name and date from the file loaded
function parse_file_name(file_name)
    -- reverse it so we can find the last instance
    file_name = string.reverse(file_name)
    file_name_pos = string.find(file_name, "\\")
    -- get the file loaded
    file_name = string.sub(file_name, 0, file_name_pos - 1)
    -- swap it back
    file_name = string.reverse(file_name)
    -- look for -DCS-
    dcs_pos = string.find(file_name, "-DCS-")
    if(dcs_pos == nil)
    then
        Tacview.Log.Info("non-DCS file loaded, bailing")
        return nil, nil
    end
    -- chop out the date
    date_start_pos = string.find(file_name, '-')
    date = string.sub(file_name, date_start_pos + 1)
    date_end_pos = string.find(date, '-')
    date = string.sub(date, 0, date_end_pos - 1)

    -- drop the extra junk at the end
    file_name = string.sub(file_name, dcs_pos + 5)
    msn_name = string.sub(file_name, 0, string.len(file_name) - 9)
    return msn_name, date
end

-- look for matching audio files for the MSN name + date combo
function find_audio(msn, date, dir)
    files = Tacview.Directory.GetFiles(
        dir .. "\\srs"
    )

    results = {}
    for i, current_file in ipairs(files) do
        msn_match = string.match(string.gsub(current_file, '-', ''), msn)
        date_match = string.match(current_file, date)
        if (msn_match and date_match) then
            Tacview.Log.Info("Found match " .. current_file)
            table.insert(results, current_file)
        end
    end
    return results
end

-- attempt to load the audio files
function load_audio(audio_file)
    if (next(audio_file) == nill) then
        Tacview.Log.Info("no valid audio -- bailing")
        return
    end
    loaded = Tacview.Media.Load(0, audio_file[1], Tacview.Context.GetAbsoluteTime())
    Tacview.Log.Info("Loaded file:")
    Tacview.Log.Info(loaded)
end

Tacview.Log.Info("Registering listeners")
-- load file listener
Tacview.Events.DocumentLoaded.RegisterListener( handle_file_load )
-- unload file listener (can be used to auto-unload the audio file)
--Events.DocumentUnload.RegisterListener( function )

