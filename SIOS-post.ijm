function action(dir, filename, includefilename) {
	print("Processing "+filename);
	
	if (endsWith(dir, File.separator) == false) {
		dir += File.separator;
	}

	open(dir+filename);	
	getPixelSize(unit, pw, ph, pd);
	
	unitchanged = false;
	if (unit == "cm") {
		print("--> Converting from cm to um");
		pw *= 10*1000;
		ph *= 10*1000;
		unitchanged = true;
	} else if (unit == "inch") {
	  print("--> Converting from inch to um");
	  pw *= 25.4*1000;
    ph *= 25.4*1000;
    unitchanged = true;
  }

  if (unitchanged == true) {
		setVoxelSize(pw, ph, 0, "um");
		save(dir+filename);
	}

	close();
	
	savewithlut(dir, filename, "Fire", "PNG", includefilename);
	savewithlut(dir, filename, "ICA", "PNG", includefilename);
}

//action(getInfo("image.directory"), getInfo("image.filename"));

macro "SIOS Post Action Tool - C000De9C000C111D3cD51D76D86C111D67D68D97D98C111D79D89C111D3dC111C222D50C222C333D3aDcaC333D61C333C444D64D94C444D35D6bD9bDc5C444D5aDaaC444D48Db8C444Df8C555D72D82C555D47Db7C555D41C555D7dC555D8dC555D55Da5De8Df7C666D07C666D4eDd9Df9C666D34DbeDc4C666D08D54Da4C666D3bD5eDaeC666D2cD7cD8cC666D46D69D99Db6C666D66D96C666C777D25Dd5C777D74D7bD84D8bC777Dc9C777D39C777D19DcdC777D91C777DdaC777D4aDbaC777D2dD32Dc2C888DcbC888D36D73D83Dc6C888DeaC888D2aC888D59Da9C888D6eD9eC888D31D60Dc1C888Db1DccC888C999D16D7aD8aDe6C999D33D49Db9Dc3C999D44Db4C999D63D6aD9aC999D40D93C999Da1C999D06D45Db5Df6C999D38CaaaDc8CaaaD4dCaaaD56Da6CaaaD3eCaaaD4cD5bDabCaaaD58D71Da8CaaaD81CaaaD15DceDe5CbbbD37Dc7CbbbD29CbbbD57Da7CbbbD75D85CbbbD6dD9dCbbbCcccD09D4bDa0CcccD6cD9cCcccDb0CcccD52CcccD2bCcccD24D62Dd4CcccDbbCcccD65D95Dd8CcccD23Dd3CcccDfaCcccDdbCdddDdcCdddD7eD8eCdddD1aCdddD18D22D92CdddDd2CdddCeeeD26Dd6CeeeDbdCeeeD90CeeeDddCeeeD42CeeeDe7CeeeCfffD17D30CfffDc0CfffD5dDadCfffD2eCfffD05Df5CfffD53Da3Db2CfffD21Dd1CfffD1cCfffD1dCfffD70CfffDdeCfffD0aD14D28D43D5cD80Da2DacDb3DbcDd7De4DebCfffD00D01D02D03D04D0bD0cD0dD0eD0fD10D11D12D13D1bD1eD1fD20D27D2fD3fD4fD5fD6fD7fD8fD9fDafDbfDcfDd0DdfDe0De1De2De3DecDedDeeDefDf0Df1Df2Df3Df4DfbDfcDfdDfeDff"{
	dir = getDirectory("Select directory containing SIOS TIFFs");
	files = getFileList(dir);
    tiffiles = filterFilesByExtension(files, '.tif');

	Dialog.create("SIOS Post Options");
	Dialog.addChoice("Include Filename", newArray("Yes", "No"));
	Dialog.show();

	includefilename = 0;
	if (Dialog.getChoice() == "Yes") {
		includefilename = 1;
	}
	
	setBatchMode(true);
	
	for (idx = 0; idx < tiffiles.length; ++idx) {
    showProgress((idx+1)/tiffiles.length);
		filename = tiffiles[idx];
    action(dir, filename, includefilename);
	}
	
	showMessage("Processing complete.");
}	
