function GUI_Gain_Callback(source, ~)          
    h = guidata(source);
    
    if source.Tag == "GainSlider"
        input = get(source, 'Value');
        input = int16(input);
        set(h.CamCtrl.gain, 'String', num2str(input));
    end
    if source.Tag == "GainEdit"
        input = get(source, 'String');
        input = str2double(input);
        set(h.CamCtrl.gainsl, 'Value', int16(input)); % double(input)
    end
    if isnan(input) || input > 24
        errordlg('You must enter a numeric value from 0 to 24','Invalid Input','modal')
        uicontrol(source)
        return
    else
        set(h.camObj, 'Gain',input)
    end

end