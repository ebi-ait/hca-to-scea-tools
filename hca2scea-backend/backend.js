const bodyParser = require('body-parser');
const cors = require('cors');
const express = require('express');
const fs = require('fs');
const multer = require('multer');
const path = require('path');

const spreadsheetTools = require('./spreadsheetTools');


const app = express();
const spreadsheetRootPath = 'spreadsheets';
app.use(cors());
app.use(bodyParser.json());

let workingDir = undefined;
let info = {};


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

    info = JSON.parse(req.body.info);
    workingDir = req.file.destination;

    spreadsheetTools.extractCSV(req.file);
    console.log('CSV Extracted');
    spreadsheetTools.saveInfo(workingDir, info);
    console.log('Info JSON saved');
    converterChildProcess = spreadsheetTools.convertSpreadsheet(workingDir, info);

    converterChildProcess.on('close', () => {
      console.log('Sheets converted');

      const projectDetails = fs.readFileSync(`${workingDir}/project_details.json`);
      return res.status(200).send(projectDetails);
    });
  });
});

// create magetab.
app.post('/createmagetab', async (req, res) => {
  upload(req, res, function (err) {
    if (err) {
      console.log('err', err);
      return res.status(500).json(err);
    }

    info = {...info, ...req.body};

    spreadsheetTools.saveInfo(workingDir, info);
    console.log('Info JSON saved');
    converterChildProcess = spreadsheetTools.createMagetab(workingDir, info);

    converterChildProcess.on('close', () => {
      console.log('Magetab created');

      return res.status(200);
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