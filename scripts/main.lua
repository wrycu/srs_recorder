
-- To communicate with Tacview, we first need to declare which interface we want to use.
-- For instance this tutorial has been programmed for Tacview 1.7.3

local Tacview = require("Tacview188")

-- Before anything else we should name our add-on

Tacview.AddOns.Current.SetTitle("SRS Recorder")
Tacview.AddOns.Current.SetVersion("0.0.1")
Tacview.AddOns.Current.SetAuthor("Wrycu")
Tacview.AddOns.Current.SetNotes("Automatically loads SRS recordings")

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

function load_audio(audio_file)
    if (next(audio_file) == nill) then
        Tacview.Log.Info("no valid audio -- bailing")
        return
    end
    if (#audio_file > 1) then
        Tacview.Log.Info("found multiple possible audio files, asking user which to load")
        -- there is more than one possible audio file to load, ask them which they want to use
        -- create the dialog object
        audio_dialog = Tacview.UI.DialogBox.Create("SRS Recorder", 200, 40, "")
        -- add helper text
        Tacview.UI.DialogBox.AddText(audio_dialog, "Multiple recorded frequencies found, please select one to load", 5, 5, 299, 10)
        for i, current_file in ipairs(audio_file) do
            -- set up the buttons for each file
            Tacview.UI.DialogBox.AddButton(
                audio_dialog,
                parse_freq(audio_file[i]) .. "Mhz",
                i * 40,
                15,
                40,
                20,
                function ()
                    -- call ourselves with the selected file and hide the dialog box
                    load_audio({audio_file[i]})
                    Tacview.UI.DialogBox.Hide(audio_dialog)
                end
            )
        end
        Tacview.UI.DialogBox.Show(audio_dialog)
    else
        loaded = Tacview.Media.Load(0, audio_file[1], Tacview.Context.GetAbsoluteTime())
        Tacview.Log.Info("Loaded file:")
        Tacview.Log.Info(loaded)
    end
end

function parse_freq(file_name)
    -- 20220714_wrycu_training_syria_v1.3_day_127.5.ogg
    return string.sub(
        file_name,
        string.len(file_name) - 8,
        string.len(file_name) - 4
    )
end

-- We can directly ask Tacview to display specific information in its log

Tacview.Log.Info("Registering listeners")
-- update file

-- load file listner
Tacview.Events.DocumentLoaded.RegisterListener( handle_file_load )
