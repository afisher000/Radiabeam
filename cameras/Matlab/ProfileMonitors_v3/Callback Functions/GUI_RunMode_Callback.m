function GUI_RunMode_Callback(source, ~)
    h = guidata(source);
    
    if source.Value
        source.String='Free run';
        stop(h.vid);            
        triggerconfig(h.vid,'manual');
        set(h.camObj, 'TriggerMode', 'Off');
        set(h.camObj, 'TriggerSource', 'Freerun');
        set(h.camObj, 'TriggerSelector', 'AcquisitionStart');
        set(h.vid, 'TriggerRepeat', Inf); 
        % set(h.camObj, 'TriggerDelayAbs', 100);
        if  ~isrunning(h.vid)
            start(h.vid);
            set(h.Pause, 'BackgroundColor', 'green');
            set(h.Pause, 'String', 'Pause Acquisition');
            set(h.Pause, 'Value', 0)
        end 
        trigger(h.vid);
        source.BackgroundColor='red';
    else
        source.String='Hardware trg'; 
        stop(h.vid);
        triggerconfig(h.vid,'hardware'); 
		set(h.camObj, 'TriggerOverlap', 'Off');	
        set(h.camObj, 'TriggerSelector', 'FrameStart');
        set(h.camObj, 'TriggerSelector', 'FrameStart'); % AcquisitionRecord FrameStart
        set(h.vid, 'FramesPerTrigger', 1); % test line. Consider to delete it
        set(h.camObj, 'TriggerMode', 'On');
        set(h.camObj, 'TriggerSource', 'Line1');
        set(h.camObj, 'TriggerActivation', 'RisingEdge');
        % set(h.camObj, 'TriggerDelayAbs', 0);	
		set(h.vid, 'TriggerRepeat', Inf)
        source.BackgroundColor='green';
        if  ~isrunning(h.vid)
            start(h.vid);
            set(h.Pause, 'BackgroundColor', 'green');
            set(h.Pause, 'String', 'Pause Acquisition');
            set(h.Pause, 'Value', 0)
        end            
    end
end