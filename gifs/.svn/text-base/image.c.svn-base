#include <stdio.h>
#include <string.h>
#include <FreeImage.h>

int main(int argc, char *argv) {
	FIMULTIBITMAP *src;
	src = FreeImage_OpenMultiBitmap(FIF_GIF, "American_Flag_ani.gif", FALSE, TRUE, FALSE, GIF_PLAYBACK);

        int count = FreeImage_GetPageCount(src);
	int page, i, row, col, background, transparent;
        RGBQUAD bkcolor;
        BYTE pixel;
        BITMAPINFOHEADER *header;

	char buffer[25*16 + 16];

        RGBQUAD *palette;

	background = 0;
	for(page = 0; page < count; page++) {
            FIBITMAP *dib = FreeImage_LockPage(src, page);
            dib = FreeImage_ConvertTo8Bits(dib);
            if(dib) {
		printf("%dx%d\n", FreeImage_GetHeight(dib), FreeImage_GetWidth(dib));
                FreeImage_GetBackgroundColor(dib, &bkcolor);
                background = (&bkcolor)->rgbReserved;
		transparent = FreeImage_GetTransparentIndex(dib);
		header  = FreeImage_GetInfoHeader(dib);
                memset(buffer, ' ', sizeof(char) * 24 * 16 + 17 * sizeof(char));

		for( row = 15; row >= 0; row-- ) {
			for( col = 0; col < 24; col++ ) {
				if ( FreeImage_GetPixelIndex(dib, col, row, &pixel) ) {
                                	//if((&pixel)->rgbRed != (&bkcolor)->rgbRed || (&pixel)->rgbGreen != (&bkcolor)->rgbGreen || (&pixel)->rgbBlue != (&bkcolor)->rgbBlue)
                                	if((int)pixel != transparent && (int)pixel != background)
						buffer[(16-row) * 25 + col] = '.';
					//printf("bkcolor: %d, r:%d, g:%d, b:%d\n", transparent, (&bkcolor)->rgbRed, (&bkcolor)->rgbGreen, (&bkcolor)->rgbBlue);
					//printf("pixel: %d, r:%d, g:%d, b:%d\n", transparent, (&pixel)->rgbRed, (&pixel)->rgbGreen, (&pixel)->rgbBlue);
				}

			}
                }
                for (row = 0; row < 16; row++) 
                        buffer[row * 25 + 25] = '\n';
                buffer[row * 25] = '\0';
		printf("-----\n%s\n-----\n", buffer);
            	FreeImage_UnlockPage(src, dib, FALSE);
            }
        }

	FreeImage_CloseMultiBitmap(src, GIF_DEFAULT);	
}
