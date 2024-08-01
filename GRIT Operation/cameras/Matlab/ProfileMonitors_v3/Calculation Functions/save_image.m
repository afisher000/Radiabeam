function save_image(h)   
    % Read image data
    A               = h.Image.CData;
    %         A               = rescale(double(A));
    
    % Create Time string (year, month, day, hour, minute, second)
    FrameAcqTime    = getappdata(h.Image,'FrameAcqTime');
    strings         = cell(1, length(FrameAcqTime));
    for j=1:length(FrameAcqTime)
        strings{j}= num2str(round(FrameAcqTime(j)), 6);
    end
    timeStr = strjoin(strings, '-');
    
    % Gain string
    gainStr         = ['Gain=', int2str(get(h.camObj, 'Gain'))];
    
    % Filter string
    filterStr       = ['Filter=', h.objIFW.filterTAG];
    
    % Combine into file_name 
    file_name       = [strjoin({timeStr, filterStr, gainStr}, '_'), '.png'];
    file_path       = fullfile(h.image_dir, file_name);
    
    % Save image
    imwrite(A, file_path, 'png', 'BitDepth',16);% CreationTi
    fprintf('Saved as %s\n', file_name);

end