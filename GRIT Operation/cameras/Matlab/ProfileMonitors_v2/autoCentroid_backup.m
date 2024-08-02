function [x0,y0,ctrtype] = autoCentroid(h,I, level)
% auto centroid finder
% h is the usual GUI handle holder
% I is an indexed grayscale image
% level is between 0 and 1 and corresponds to the 

    % gaussian blur image to eliminate hot-spots
    mask=fspecial('disk',5);  % blur out noise that causes local extrema. Increase number for more resistance
    If=imfilter(I,mask);        % Filter the image

    Ibw = imbinarize(If);      %convert to binary image
    Ibw = imfill(Ibw,'holes');  %fill in holes in donuts
    % Ibw=imregionalmax(I);
    % Ibw=imhmax(I,0.4);

    stat = regionprops(bwlabel(Ibw),'centroid');
        % stat contains the centroid information. The centroid method can
        % give multiple centroids
    
    [ny, nx]=size(I);    
    if numel(stat)==0        % if no centroids were found
        x0=round(nx/2);     % then use the very center of the image
        y0=round(ny/2);
        disp("No peaks found; using image center")
        ctrtype="image center";
    elseif numel(stat)==1
        x0=round(stat(numel(stat)).Centroid(1));
        y0=round(stat(numel(stat)).Centroid(2));
        ctrtype="automatic";
    else            % more than one centroid found
%         for x = 1: numel(stat)        %plot all of the centroids
%             plot(stat(x).Centroid(1),stat(x).Centroid(2),'go');
%             x0=stat(x).Centroid(1);
%             y0=stat(x).Centroid(2);
%         end
        x0=round(nx/2);     % then use the very center of the image
        y0=round(ny/2);
        disp('Inconclusive centroid; using image center')
        ctrtype='image center';
    end
end