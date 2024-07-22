function out = Makocaller(deviceID)
%   This function is intended to be generic for every Mako camera. There
%   are some settings that are different for each camera, but those can be
%   set to a different value in the calling function.
%   The DeviceID
%   
%   This is the machine generated representation of a video input object.
%   This MATLAB code file, 20210318-MAKOTESTER-MONO8-10HZ.M, was generated from the OBJ2MFILE function.
%   A MAT-file is created if the object's UserData property is not 
%   empty or if any of the callback properties are set to a cell array  
%   or to a function handle. The MAT-file will have the same name as the 
%   code file but with a .MAT extension. To recreate this video input object,
%   type the name of the code file, 20210318-MakoTester-Mono8-10Hz, at the MATLAB command prompt.
%   
%   The code file, 20210318-MAKOTESTER-MONO8-10HZ.M and its associated MAT-file, 20210318-MAKOTESTER-MONO8-10HZ.MAT (if
%   it exists) must be on your MATLAB path.
%   
%   Example: 
%       vidobj = 20210318-MakoTester-Mono8-10Hz;
%   
%   See also VIDEOINPUT, IMAQDEVICE/PROPINFO, IMAQHELP, PATH.
%   

% Check if we can check out a license for the Image Acquisition Toolbox.
canCheckoutLicense = license('checkout', 'Image_Acquisition_Toolbox');

% Check if the Image Acquisition Toolbox is installed.
isToolboxInstalled = exist('videoinput', 'file');

if ~(canCheckoutLicense && isToolboxInstalled)
    % Toolbox could not be checked out or toolbox is not installed.
    error(message('imaq:obj2mfile:invalidToolbox'));
end

% Load the MAT-file containing UserData and CallBack property values.
try
    MATvar = load('20210318-MakoTester-Mono8-10Hz');
    MATLoaded = true;
catch
    warning(message('imaq:obj2mfile:MATload'));
   MATLoaded = false;
end


% Device Properties.
adaptorName = 'gige';
% deviceID = 1;
vidFormat = 'Mono10';
tag = '';

% Search for existing video input objects.
existingObjs1 = imaqfind('DeviceID', deviceID, 'VideoFormat', vidFormat, 'Tag', tag);

if isempty(existingObjs1)
    % If there are no existing video input objects, construct the object.
    vidObj1 = videoinput(adaptorName, deviceID, vidFormat);
else
    % There are existing video input objects in memory that have the same
    % DeviceID, VideoFormat, and Tag property values as the object we are
    % recreating. If any of those objects contains the same AdaptorName
    % value as the object being recreated, then we will reuse the object.
    % If more than one existing video input object contains that
    % AdaptorName value, then the first object found will be reused. If
    % there are no existing objects with the AdaptorName value, then the
    % video input object will be created.

    % Query through each existing object and check that their adaptor name
    % matches the adaptor name of the object being recreated.
    for i = 1:length(existingObjs1)
        % Get the object's device information.
        objhwinfo = imaqhwinfo(existingObjs1{i});
        % Compare the object's AdaptorName value with the AdaptorName value
        % being recreated.
        if strcmp(objhwinfo.AdaptorName, adaptorName)
            % The existing object has the same AdaptorName value as the
            % object being recreated. So reuse the object.
            vidObj1 = existingObjs1{i};
            % There is no need to check the rest of existing objects.
            % Break out of FOR loop.
            break;
        elseif(i == length(existingObjs1))
            % We have queried through all existing objects and no
            % AdaptorName values matches the AdaptorName value of the
            % object being recreated. So the object must be created.
            vidObj1 = videoinput(adaptorName, deviceID, vidFormat);
        end %if
    end %for
end %if

% Configure properties whose values are saved in 
% C:\Users\Marcos\RadiaBeam Technologies, LLC\GRIT-Hybrid Gun Test Stand - Documents\Controls and Interfacing\ProfileMonitor Imaging\20210318-MakoTester-Mono8-10Hz.mat.
if (MATLoaded)
    % MAT-file loaded successfully. Configure the properties whose values
    % are saved in the MAT-file.
    set(vidObj1, 'ErrorFcn', MATvar.errorfcn1);
else
   % MAT-file could not be loaded. Configure properties whose values were
   % saved in the MAT-file to their default value.
    set(vidObj1, 'ErrorFcn', @imaqcallback);
end

framesToAcquire = 1;

% Configure vidObj1 properties.

set(vidObj1, 'IgnoreDroppedFrames', 'on');
set(vidObj1, 'FramesPerTrigger', framesToAcquire);            % can also be modified on the fly in the future
set(vidObj1, 'TriggerRepeat', Inf);
srcObj1 = get(vidObj1, 'Source');
set(srcObj1(1), 'StreamBytesPerSecond', 1e+08); % FOR 1 GBit router
set(srcObj1(1), 'StreamFrameRateConstrain', 'TRUE');
srcObj1.addprop('AutoSave');
srcObj1.AutoSave = false;
srcObj1.addprop('Threshold');
srcObj1.addprop('BitDepth');
if get(vidObj1, 'VideoFormat') == "Mono10"
        srcObj1.BitDepth=10;
end
if get(vidObj1, 'VideoFormat') == "Mono8"
        srcObj1.BitDepth=8;
end

srcObj1.Threshold = 0;
srcObj1.PacketSize = 8000; % setting this value above 8000 will cause errors and frames loss

% framesPerSecond = CalculateFrameRate(vidObj1, framesToAcquire);
% works bad for some cameras. The otimal value is 8 for 5 camers and 1 Gige
% ethernet connection
framesPerSecond = 10;
AcquisitionFrameRateLimit = get(srcObj1(1), 'AcquisitionFrameRateLimit');
if (framesPerSecond > AcquisitionFrameRateLimit)
    framesPerSecond = AcquisitionFrameRateLimit;
end
packetDelay = CalculatePacketDelay(vidObj1, framesPerSecond);
set(srcObj1(1), 'AcquisitionFrameRateAbs', framesPerSecond);
set(srcObj1(1), 'PacketSize', srcObj1.PacketSize);
srcObj1.ReverseX= 'True';


% Configure vidObj1's video source properties.
% set(srcObj1(1), 'BalanceRatioAbs', '(Currently not accessible)');
% set(srcObj1(1), 'BalanceRatioSelector', '(Currently not accessible)');
% set(srcObj1(1), 'BalanceWhiteAuto', '(Currently not accessible)');
% set(srcObj1(1), 'BalanceWhiteAutoAdjustTol', '(Currently not accessible)');
% set(srcObj1(1), 'BalanceWhiteAutoRate', '(Currently not accessible)');
% set(srcObj1(1), 'ColorTransformationMode', '(Currently not accessible)');
% set(srcObj1(1), 'ColorTransformationSelector', '(Currently not accessible)');
% set(srcObj1(1), 'ColorTransformationValue', '(Currently not accessible)');
% set(srcObj1(1), 'ColorTransformationValueSelector', '(Currently not accessible)');
% set(srcObj1(1), 'DeviceTemperature', 47.718);
set(srcObj1(1), 'ExposureAuto', 'Off');
set(srcObj1(1), 'ExposureTimeAbs', 1000);
set(srcObj1(1), 'GainAuto', 'Off');
set(srcObj1(1), 'Gain', 0.0);
% set(srcObj1(1), 'Hue', '(Currently not accessible)');
% set(srcObj1(1), 'ImageSize', 1.31072e+06);
% set(srcObj1(1), 'IrisAutoTarget', '(Currently not accessible)');
% set(srcObj1(1), 'IrisMode', '(Currently not accessible)');
% set(srcObj1(1), 'IrisVideoLevel', '(Currently not accessible)');
% set(srcObj1(1), 'IrisVideoLevelMax', '(Currently not accessible)');
% set(srcObj1(1), 'IrisVideoLevelMin', '(Currently not accessible)');
% set(srcObj1(1), 'LensDCDriveStrength', '(Currently not accessible)');
% set(srcObj1(1), 'LensPIrisFrequency', '(Currently not accessible)');
% set(srcObj1(1), 'LensPIrisNumSteps', '(Currently not accessible)');
% set(srcObj1(1), 'LensPIrisPosition', '(Currently not accessible)');
% set(srcObj1(1), 'Saturation', '(Currently not accessible)');
% set(srcObj1(1), 'SensorDigitizationTaps', '(Currently not accessible)');
% set(srcObj1(1), 'SensorTaps', '(Currently not accessible)');
% set(srcObj1(1), 'StreamBytesPerSecond', 2e+07); % FOR 1 GBit router
% set(srcObj1(1), 'StreamFrameRateConstrain', 'TRUE');
% set(srcObj1(1), 'StreamBytesPerSecond', 1e+06);  % For 100 MBit router
% set(srcObj1(1), 'StreamHoldCapacity', 48);
% set(srcObj1(1), 'VsubValue', '(Currently not accessible)');

% set(srcObj1(1), 'AcquisitionMode', 'Continuous');

%%% LED Control section %%%
set(srcObj1(1), 'SyncOutSource', 'GPO');
set(srcObj1(1), 'SyncOutSelector', 'SyncOut1');
set(srcObj1(1), 'SyncOutPolarity', 'normal');
set(srcObj1(1), 'SyncOutLevels', 0);

%%% Freerun Configuration %%%
% triggerconfig(vidObj1,'manual');
% set(srcObj1(1), 'TriggerMode', 'Off');
% set(srcObj1(1), 'TriggerSource', 'Freerun'); 
% set(srcObj1(1), 'TriggerSelector', 'AcquisitionStart');
% set(srcObj1(1), 'TriggerOverlap', 'Off');

%%% Trigger Configuration %%%
triggerconfig(vidObj1,'hardware'); 
set(vidObj1, 'FramesPerTrigger', 1); % test line. Consider to delete it
set(srcObj1(1), 'TriggerOverlap', 'Off');			
set(srcObj1(1), 'TriggerSelector', 'FrameStart'); % AcquisitionRecord FrameStart
set(srcObj1(1), 'TriggerMode', 'On');
set(srcObj1(1), 'TriggerSource', 'Line1');
set(srcObj1(1), 'TriggerActivation', 'RisingEdge');
set(srcObj1(1), 'TriggerDelayAbs', 0);	
set(vidObj1, 'TriggerRepeat', Inf)

out = vidObj1 ;
