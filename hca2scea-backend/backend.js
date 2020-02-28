const cors = require('cors');
const express = require('express');
const fs = require('fs');
const multer = require('multer');
const path = require('path');

const spreadsheetTools = require('./spreadsheetTools');


const app = express();
const spreadsheetRootPath = 'spreadsheets';
app.use(cors());


// Multer instance.
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const spreadsheetPath = `${spreadsheetRootPath}/${file.originalname.split('.')[0]}`;

    fs.mkdirSync(spreadsheetPath, { recursive: true });
    cb(null, spreadsheetPath);
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname);
  }
});

const upload = multer({ storage: storage }).single('file');


// Serve web.
app.use(express.static(path.join(__dirname, '/public')));

// convert xlsx.
app.post('/convertxlsx', async (req, res) => {
  upload(req, res, function (err) {
    if (err) {
      console.log('err', err);
      return res.status(500).json(err);
    }

    const info = JSON.parse(req.body.info);

    spreadsheetTools.extractCSV(req.file);
    console.log('CSV Extracted');
    spreadsheetTools.saveInfo(req.file.destination, info);
    console.log('Info JSON saved');
    converterChildProcess = spreadsheetTools.convertSpreadsheet(req.file.destination, info);

    converterChildProcess.on('close', () => {
      console.log('Sheets converted');

      const protocolMap = fs.readFileSync(`${req.file.destination}/protocol_map.json`);
      return res.status(200).send(protocolMap);
    });
  });
});

// Handle other requests by serving the web too.
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname+'/public/index.html'));
});


// Start server.
const port = process.env.PORT || 5000;
app.listen(port);

console.log('App is listening on port ' + port);