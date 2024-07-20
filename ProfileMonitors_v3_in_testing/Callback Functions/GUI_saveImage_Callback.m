function GUI_saveImage_Callback(source,~)
% Gets data from the main viewing axis and saves a full-depth and 8-bit
% depth image. Filenames correspond to the frame acquisition time with
% milliseconds.

    h = guidata(source);
    save_image(h)

end