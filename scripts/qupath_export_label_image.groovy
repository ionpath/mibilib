import qupath.lib.regions.*
import ij.*
import java.awt.*
import java.awt.image.BufferedImage
import javax.imageio.ImageIO

def server = getCurrentImageData().getServer()
int w = server.getWidth()
int h = server.getHeight()

int[][] labelArray = new int[h][w]

int index = 1
for (detection in getDetectionObjects()) {
    roi = detection.getROI()
    
    for (int y = (int)roi.getBoundsY(); y <= (int)(roi.getBoundsY() + roi.getBoundsHeight()); y++){
        for (int x = (int)roi.getBoundsX(); x <= (int)(roi.getBoundsX() + roi.getBoundsWidth()); x++) {
            if (roi.contains(x, y)) {
                labelArray[y][x] = index
            }
        }
    }    
    index++
}

def labelImage = new BufferedImage(w, h, BufferedImage.TYPE_USHORT_GRAY)

def g2d = labelImage.createGraphics()

for (int y = 0; y < h; y++) {
    for (int x = 0; x < w; x++) {
        labelValue = labelArray[y][x]
        labelImage.getRaster().setPixel(x, y, labelValue)
    }
}

g2d.dispose()

new ImagePlus('Labels', labelImage).show()

def projectDirectory = getProjectBaseDirectory()
def imageName = getProjectEntry().getImageName()
def fileoutput = new File(projectDirectory, imageName + '-labels.png')
ImageIO.write(labelImage, 'png', fileoutput)
