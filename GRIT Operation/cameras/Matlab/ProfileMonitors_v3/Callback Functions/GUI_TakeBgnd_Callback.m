    function GUI_TakeBgnd_Callback(source, ~)
        h = guidata(source);
        
        set(h.SubtBgnd,'UserData',h.Image.CData)
    end