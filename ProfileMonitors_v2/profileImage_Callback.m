function profileImage_Callback(~,~,h)
%         stoppreview(vid)
    h.rpos=imrect(h.axes);
    rpv=wait(h.rpos);
    rpv=round(rpv);
    [prof.cx, prof.cy, prof.c]=improfile;

        xspan=rpv(1):rpv(1)+rpv(3)*1.5;
        yspan=rpv(2):rpv(2)+rpv(4)*1.5;
%         C=imadjust(A,stretchlim(A(yspan,xspan)));
%         [prof.cx prof.cy prof.c]=improfile(C,prof.cx,prof.cy);

    hlocfig=figure('PaperPositionMode','auto');

%         while h.profile.Value==1

        A=getimage(h.axes);
        B=A(yspan,xspan);
        subplot(10,1,1:6);
        maxVal=max(max(B));
        minVal=min(min(B));
            cm=gray(256);cm(end,2:3)=0;cm(end,1)=1;
                        cm(1:2,[1,3])=0;cm(1,2)=1;
        %colormap(cm)
        colormap('bone')
        imagesc([min(xspan) max(xspan)],[min(yspan) max(yspan)],...
                B,[0,255]);hold on;colorbar
        line([prof.cx(1) prof.cx(end)],[prof.cy(1) prof.cy(end)]);
        axis image;
%             axis([0.5 0.5+vidRes(1) 0.5 0.5+vidRes(2)])
        grid on
        elespan=sqrt((prof.cx(end)-prof.cx(1)).^2 + (prof.cy(end)-prof.cy(1))^2);

        subplot(10,1,8:10);
        maxnum=elespan/length(prof.c);
        plot((1:length(prof.c))*maxnum,prof.c/255);ylim([0,1]);
        set(gca,'YTick',[0 .2 .5 .8 1])
        grid on

%         set(hlocfig,'Visible','on')
end