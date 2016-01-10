function action(dir, filename) {
	print("Processing "+filename);
	
	if (endsWith(dir, File.separator) == false) {
		dir += File.separator;
	}

	savewithlut(dir, filename, "Grays", "TIF", true, false);
	savewithlut(dir, filename, "Grays", "PNG", true, false);
}

//action(getInfo("image.directory"), getInfo("image.filename"));

macro "ND2 To Tif Action Tool - C000D02D03D04D05D06D07D08D09D0aD0bD0cD12D13D14D25D26D27D28D29D3aD3bD3cD42D43D44D45D46D47D48D49D4aD4bD4cD62D63D64D65D66D67D68D69D6aD6bD6cD72D7cD83D8bD94D95D96D97D98D99D9aDb2Db3Db4Db9DbaDbbDbcDc2Dc8DccDd2Dd8DdcDe2De7DecDf2Df3Df4Df5Df6DfbDfcC000C111C222C333C444C555C666C777C888C999CaaaCbbbCcccCdddCeeeCfff" {
	dir=getDirectory("Select directory containing ND2s");
	files=getFileList(dir);
  nd2files=filterFilesByExtension(files, ".nd2");

	setBatchMode(true);
	showProgress(0);
	for (idx = 0; idx < nd2files.length; ++idx) {
		showProgress((idx+1)/nd2files.length);
		filename = nd2files[idx];
    action(dir, filename);
	}
	
	showMessage("Processing complete.")
}	
