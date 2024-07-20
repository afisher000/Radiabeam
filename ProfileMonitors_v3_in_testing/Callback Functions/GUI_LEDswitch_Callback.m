function GUI_LEDswitch_Callback(source, ~)
    h = guidata(source);
    
    if source.Value     % if button is depressed, then execute command
        source.String='LED is on';
        set(h.camObj, 'SyncOutLevels', 1);
    else            
        source.String='LED is off';
        set(h.camObj, 'SyncOutLevels', 0);
    end    
end