function [x0,y0,ctrtype] = autoCentroid(h,I, level)
% auto centroid finder
% h is the usual GUI handle holder
% I is an indexed grayscale image
% level is between 0 and 1 and corresponds to the 

    % gaussian blur image to eliminate hot-spots
    mask=fspecial('disk',10);  % blur out noise that causes local extrema. Increase number for more resistance
    If=imfilter(I,mask);        % Filter the image
% If=I;
    Ibw = imbinarize(If,level);      %convert to binary image
    Ibw = imfill(Ibw,'holes');  %fill in holes in donuts
    % Ibw=imregionalmax(I);
    % Ibw=imhmax(I,0.4);

    stat = regionprops(logical(Ibw));
        % stat contains the centroid information. The centroid method can
        % give multiple centroids
%     disp(numel(stat))
%     [ny, nx]=size(I);    
    if numel(stat)==0        % if no centroids were found
        x0=-2;     
        y0=-2;
%         disp("No peaks found; using image center")
        ctrtype="None";
    elseif numel(stat)==1   %only one centroid is found. Great!
        x0=round(stat(numel(stat)).Centroid(1));
        y0=round(stat(numel(stat)).Centroid(2));
        ctrtype="automatic";
    else            % more than one centroid found. pick the one with largest area
        [~,index] = max([stat.Area]);
        x0=round(stat(index).Centroid(1));
        y0=round(stat(index).Centroid(2));
        ctrtype = "multiple";
    end
end