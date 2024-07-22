function GUI_autoGain_Callback(source, ~)
    h = guidata(source);
    if source.Value     % if button is depressed, then execute command
        set(h.camObj, 'GainAuto', 'Once');
        source.String='autoGain';
    else
        set(h.camObj, 'GainAuto', 'Off');
        source.String='autoGain';
    end    
end