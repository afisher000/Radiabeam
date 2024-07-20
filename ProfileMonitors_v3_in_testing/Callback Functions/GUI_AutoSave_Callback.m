function GUI_AutoSave_Callback(source, ~)
    h = guidata(source);
    stop(h.vid);

    % True if button depressed
    if source.Value 
        source.String='AutoSave ON';
        set(h.camObj, 'AutoSave', true);
    else            
        source.String='AutoSave OFF';            
        h.autoSave = false; 
        set(h.camObj, 'AutoSave', false);
    end
    
    if  ~isrunning(h.vid)
        start(h.vid);
    end
    trigger(h.vid);
end