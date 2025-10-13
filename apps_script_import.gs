// Optional Google Sheets script to import CSV later
function importCSVFromRepo() {
  var url = 'https://raw.githubusercontent.com/YOURUSER/YOURREPO/main/scan_output.csv';
  var resp = UrlFetchApp.fetch(url);
  var csv = Utilities.parseCsv(resp.getContentText());
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  sheet.clearContents();
  sheet.getRange(1,1,csv.length,csv[0].length).setValues(csv);
}