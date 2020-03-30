# HCA-TO-SCEA Tools

This repo contains various tools to help on the task of converting HCA spreadsheets to SCEA magetab files.

## hca2scea tool installation

Prerequisites: [npm](https://www.npmjs.com/), [pip](https://pypi.org/project/pip/) and the _pip_ package [virtualenv](https://virtualenv.pypa.io/en/latest/).

Once those are ready, to install the application run:

```
cd hca2scea-backend
./install.sh
```

## hace2scea tool execution

In the same hca2scea-backend directory, run:

```
npm start
```

And then, head to [http://127.0.0.1:5000]() on a browser.

Once run, the application will save the `idf` and `sdrf` parts of the magetab, along with any intermediate files used in the process into the folder `./hca2scea-backend/spreadsheets/<spreadsheet_name>/`.