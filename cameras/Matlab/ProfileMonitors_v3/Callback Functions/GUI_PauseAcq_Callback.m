function GUI_PauseAcq_Callback(source, ~)
    h = guidata(source);
    
    if source.Value     % if button is depressed, then execute command
        if isrunning(h.vid)
            stop(h.vid);
            source.String='Acquisition Paused';
            source.BackgroundColor='red';
        end
    else
        if  ~isrunning(h.vid)
            start(h.vid);
        end 
        if triggerconfig(h.vid).TriggerType == "manual"
            trigger(h.vid);
        end
        source.String='Pause Acquisition';
        source.BackgroundColor='green';
    end    
end