import shutil
from os import listdir
from os.path  import isfile, join
from os import walk
import videoTasks
from dirConfig import srcDir, encDir, outDir


f = []
for (dirpath, dirnames, filenames) in walk (srcDir):
	f.extend(filenames)

for file in f:
	shutil.move(srcDir+file, encDir+file)
	srcFile = encDir+file
	videoTasks.encode.delay(srcFile, outDir)