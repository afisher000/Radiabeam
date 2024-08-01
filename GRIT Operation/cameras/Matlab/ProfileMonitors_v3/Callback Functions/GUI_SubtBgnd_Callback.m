function GUI_SubtBgnd_Callback(source, ~)
    h = guidata(source);
    
    if source.Value     % if button is depressed, then execture command
       
        if isempty(source.UserData)   %check if the user data where the background image is stored is missing
            warndlg('Please create a background image first, then try again',...
                    'Invalid','modal');
            source.Value=source.Min;   % set the toggle button to off
            return
        end
        source.String='Subtracting Bkgnd';
        set(h.CamCtrl.shutter, 'Enable', 'off');
        set(h.CamCtrl.gain, 'Enable', 'off');
        set(h.CamCtrl.BlackLevel, 'Enable', 'off');
        set(h.CamCtrl.Threshold, 'Enable', 'on');
        set(h.CamCtrl.autoGain, 'Enable', 'off');
    else
        source.String='Subtract Background';
        set(h.CamCtrl.shutter, 'Enable', 'on');
        set(h.CamCtrl.gain, 'Enable', 'on');
        set(h.CamCtrl.BlackLevel, 'Enable', 'on');
        set(h.CamCtrl.Threshold, 'Enable', 'off');
        set(h.camObj, 'Threshold', 0);
        set(h.CamCtrl.Threshold, 'String', '0');
        set(h.CamCtrl.autoGain, 'Enable', 'on');
    end
    
end