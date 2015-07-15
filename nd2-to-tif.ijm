function drawshadowedtext(text, x, y) {
	setColor(0, 0, 0);	
	Overlay.drawString(text, x+1, y+1);
	setColor(255, 255, 255);	
	Overlay.drawString(text, x, y);
	updateDisplay();
}

function savewithlut(dir, filename, lut) {
	run("Bio-Formats Windowless Importer", "open="+dir+filename);
	
	namenoext = substring(filename, 0, indexOf(filename, ".nd2"));

	fontsize=14;
	setFont("SansSerif", fontsize, "bold");

	run(lut);
	//run("Calibration Bar...", "location=[Upper Right] fill=White label=Black number=5 decimal=0 font=12 zoom=1 overlay");
	run("Scale Bar...", "width=1000 height=4 font=14 color=White background=None location=[Lower Right] bold overlay");
	drawshadowedtext(namenoext, 0, fontsize);
	
	wait(400);
	
	print("--> Saving with LUT="+lut);
	saveAs("PNG", dir  + namenoext+"-"+lut+".png");

	close();	
}

function action(dir, filename) {
	print("Processing "+filename);
	
	if (endsWith(dir, File.separator) == false) {
		dir += File.separator;
	}

	savewithlut(dir, filename, "Grays");
}

//action(getInfo("image.directory"), getInfo("image.filename"));

macro "ND2 To Tif Action Tool - C000D02D03D04D05D06D07D08D09D0aD0bD0cD12D13D14D25D26D27D28D29D3aD3bD3cD42D43D44D45D46D47D48D49D4aD4bD4cD62D63D64D65D66D67D68D69D6aD6bD6cD72D7cD83D8bD94D95D96D97D98D99D9aDb2Db3Db4Db9DbaDbbDbcDc2Dc8DccDd2Dd8DdcDe2De7DecDf2Df3Df4Df5Df6DfbDfcC000C111C222C333C444C555C666C777C888C999CaaaCbbbCcccCdddCeeeCfff" {
	dir=getDirectory("Select directory containing ND2s");
	files=getFileList(dir);

	setBatchMode(true);
	showProgress(0);
	for (idx = 0; idx < files.length; ++idx) {
		filename = files[idx];
		if (endsWith(filename, '.nd2')) {
			action(dir, filename);
		}
		showProgress((idx+1)/files.length);
	}
	
	showMessage("Processing complete.")
}	
