const fs = require('fs');
const XLSX = require('xlsx');
const execFile = require("child_process").execFile;


convertToSnakecase = (label) => label.replace(/(\s-\s)|\s/g, '_').toLowerCase();


function convertSpreadsheet(csvPath, info) {
  console.log('converting HCA spreadsheet from', csvPath);

  return execFile('./hca-to-scea.sh', [csvPath], (err, stdout, stderr) => { console.log(stdout, stderr);});
}


function extractCSV(spreadsheetFile) {
  console.log('extracting CSV sheets from', spreadsheetFile.originalname);

  const workbook = XLSX.readFile(spreadsheetFile.path);
  var sheetList = workbook.SheetNames;

  console.log('sheets in that XLS:', sheetList);

  sheetList.forEach(sheet => {
    const worksheet = workbook.Sheets[sheet];
    const sheetCSV = XLSX.utils.sheet_to_csv(worksheet, {FS: ';', blankrows: false});

    fs.writeFile(`${spreadsheetFile.destination}/${convertToSnakecase(sheet)}.csv`, sheetCSV, (err) => { if (err) console.error(err); });
  });
}


function saveInfo(infoPath, info) {
  fs.writeFileSync(`${infoPath}/info.json`, JSON.stringify(info, null, 2));
}


module.exports = {
  convertSpreadsheet,
  extractCSV,
  saveInfo,
};
