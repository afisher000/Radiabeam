function GUI_AvgImageToggle_Callback(source, ~)
    h = guidata(source);
    
    % This was wrong? SHould be changing FramesAcquiredFcnCount property,
    % not FramesPerTrigger.

    stop(h.vid);
    if source.Value     % if button is depressed, then execture command
        set(h.vid, 'FramesPerTrigger', 5);
%         set(h.vid, 'FramesAcquiredFcnCount', 5);
        source.String='Averaging';
    else
        set(h.vid, 'FramesPerTrigger', 1);
%         set(h.vid, 'FramesAcquiredFcnCount', 5);
        source.String='AverageImages';            
    end
    if  ~isrunning(h.vid)
        start(h.vid);
    end 
    if triggerconfig(h.vid).TriggerType == "manual"
        trigger(h.vid);
    end
end