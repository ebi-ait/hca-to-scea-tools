import React from 'react';
import axios from 'axios';

import Config from './config';

import { calculateNewPoolIds, fixProtocolMap } from './tools';

import InputList from './components/InputList';
import ProtocolMatcher from './components/ProtocolMatcher';


class ConverterApp extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      spreadsheetFile: undefined,
      accession: undefined,
      curators: undefined,
      forceProjectUuid: undefined,
      requiredFields: ['spreadsheetFile', 'accession', 'curators'],
      errors: [],
      protocolMap: undefined,
      protocolTypes: [],
      globalProtocolPoolList: [],
      newPoolIdMap: {},
    };
  }

  handleChangeSpreadsheetFile = (e) => {
    this.setState({ spreadsheetFile: e.target.files[0] });
  };

  handleChangeAccession = (e) => {
    this.setState({ accession: e.target.value });
  };

  handleChangeCurators = (curators) => {
    this.setState({ curators });
  };

  handleChangeforceProjectUuid = (e) => {
    this.setState({ forceProjectUuid });
  };

  handleClickProcess = async () => {
    const { accession, curators, spreadsheetFile } = this.state;
    const errors = this.checkErrors();

    this.setState({ errors });

    if (!errors.length) {
      const spreadsheetData = new FormData();
      spreadsheetData.append('file', spreadsheetFile);
      spreadsheetData.append('info', JSON.stringify({ accession, curators }));

      const res = await axios.post(`${Config.backendUrl}/${Config.convertSpreadsheetEndPoint}`, spreadsheetData);
      const protocolTypes = Object.keys(res.data);
      const protocolMap = fixProtocolMap(res.data, protocolTypes);

      // Creates a mapping of all poolIds to their newPoolId, which originally is the same poolId.
      const newPoolIdMap = protocolTypes
        .reduce((acc, protocolType) => [...acc, ...Object.keys(protocolMap[protocolType])], [])
        .reduce((acc, poolId) => ({...acc, [poolId]: poolId}), {});

      this.setState({protocolMap, protocolTypes, newPoolIdMap });
    }
  };


  checkErrors = () => this.state.requiredFields.reduce((errors, key) => this.state[key] ? errors : [...errors, key], []);

  poolIdUpdater = () => {
    const { protocolMap, protocolTypes, newPoolIdMap } = this.state;

    this.setState({ newPoolIdMap: calculateNewPoolIds(protocolMap, protocolTypes, newPoolIdMap) });
  };


  render() {
    const {
      poolIdUpdater,
      state: { errors, protocolMap, newPoolIdMap, protocolTypes }
    } = this;

    return (
      <>
        <header>
            <h1>HCA Spreadsheet to SCEA MAGE-TAB converter</h1>
        </header>

        <div>
          <h2>First part: Preparation</h2>

          <div>
            <h3>1. Select a spreadsheet file</h3>
            <input
              type="file"
              id="spreadsheet-file-input"
              name="spreadsheetFile"
              onChange={this.handleChangeSpreadsheetFile}
              accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            />
            {errors.includes('spreadsheetFile') && <p>Select a spreadsheet file!</p>}
          </div>

          <div>
            <h3>2. Accession information</h3>
            E-HCAD-<input
              type="number"
              min="0"
              max="9999"
              size="4"
              name="accession"
              onChange={this.handleChangeAccession}
            />
            {errors.includes('accession') && <p>Enter an accession number for the submission!</p>}
          </div>

          <div>
            <h3>3. Curators</h3>
            <InputList
              type="text"
              source={this.state.curators}
              changeHandler={this.handleChangeCurators}
              defaults={['AD', 'JFG']}
            />
            {errors.includes('curators') && <p>Enter at least one curator!</p>}
          </div>

          <div>
            <h3>4. Force a Project UUID (detail this)</h3>
            <input
              type="text"
              source={this.state.forceProjectUuid}
              onChange={this.handleChangeforceProjectUuid}
            />
          </div>

          <div>
            <button
              onClick={this.handleClickProcess}
            >
              Process!
            </button>
          </div>
        </div>


        <div>
          <h2>Second part: Protocol matching</h2>
          {
            !protocolTypes.length ?
              <p>Waiting for Part 1...</p>
            :
            <>
              <p>This are the protocols coming from HCA, matched to their corresponding SCEA protocol ID.</p>
              {protocolTypes.map(protocolType =>
                <ProtocolMatcher
                  key={`protocolmatcher-${protocolType}`}
                  protocolType={protocolType}
                  protocolMap={protocolMap[protocolType]}
                  newPoolIdMap={newPoolIdMap}
                  poolIdUpdater={poolIdUpdater}
                />
              )}
            </>
          }
        </div>
      </>
    );
  }
}


export default ConverterApp;
