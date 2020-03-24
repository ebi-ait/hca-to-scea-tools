import React from 'react';
import axios from 'axios';
import moment from 'moment';

import Config from './config';

import { calculateNewPoolIds, fixProtocolMap, json2Dict, revertProtocolMap } from './tools';

import InputList from './components/InputList';
import ProtocolMatcher from './components/ProtocolMatcher';
import ConfigurableField from './components/ConfigurableField';


class ConverterApp extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      spreadsheetFile: undefined,
      accession: undefined,
      curators: undefined,
      projectUuid: undefined,
      requiredFields: ['spreadsheetFile', 'accession', 'curators'],
      errors: [],
      protocolMap: undefined,
      protocolTypes: [],
      globalProtocolPoolList: [],
      newPoolIdMap: {},
      projectData: undefined,
      processed: false,
      configurableFields: [],
    };
  }

  handleChangeAccession = e => {
    this.setState({ accession: e.target.value });
  };

  handleChangeConfigurableField = e => {
    const { configurableFields } = this.state;
    const eventOriginatorName = e.target.name;
    const newValue = e.target.value;
    const newConfigurableFields = [...configurableFields];
    const configurableFieldToChange = newConfigurableFields.find(configurableField => configurableField.name === eventOriginatorName);
    configurableFieldToChange.value = newValue;

    this.setState({ configurableFields: newConfigurableFields });
  };

  handleChangeCurators = curators => {
    this.setState({ curators });
  };

  handleChangeProjectUuid = e => {
    this.setState({ projectUuid: e.target.value });
  };

  handleClickFetchProjectDetailsAgain = () => {
    this.fetchProjectData();
  };

  handleClickSkipFetchProjectDetails = e => {
    this.setState({ projectData: {
      submissionDate: '',
      lastUpdateDate: '',
      geoAccessions: [],
    } });
  };

  handleClickFinishButton = async () => {
    const { configurableFields, projectUuid, projectData, protocolMap, protocolTypes, newPoolIdMap } = this.state;

    const projectDetails = {
      projectUuid,
      ...projectData,
      protocolMap: revertProtocolMap(protocolMap, protocolTypes, newPoolIdMap),
      configurableFields,
    };

    console.log('projectDetails outgoing', projectDetails);
    const res = await axios.post(`${Config.backendUrl}/${Config.createMagetabMappingEndpoint}`, json2Dict(projectDetails));
    const endResult = res.data;
    console.log('endResult', endResult);
  };

  handleClickProcess = async () => {
    const {
      fetchProjectData,
      state: { accession, curators, spreadsheetFile }
    } = this;
    const errors = this.checkErrors();

    this.setState({ errors });

    if (!errors.length) {
      this.setState({ processed: true });

      const spreadsheetData = new FormData();
      spreadsheetData.append('file', spreadsheetFile);
      spreadsheetData.append('info', JSON.stringify({ accession, curators }));

      const res = await axios.post(`${Config.backendUrl}/${Config.convertSpreadsheetEndpoint}`, spreadsheetData);
      const projectDetails = res.data;

      console.log('projectDetails incoming', projectDetails);

      const protocolTypes = Object.keys(projectDetails.protocol_map);
      const protocolMap = fixProtocolMap(projectDetails.protocol_map);
      const projectUuid = projectDetails.project_uuid;
      const configurableFields = projectDetails.configurable_fields;

      // Create configurable fields default.
      configurableFields.forEach(configurableField => configurableField.value = typeof configurableField.source === 'string' ? configurableField.source : configurableField.source[0]);

      this.setState({ projectUuid }, () => {
        // Gets project details from ingest API.
        fetchProjectData();

        // Creates a mapping of all poolIds to their newPoolId, which originally is the same poolId.
        const newPoolIdMap = protocolTypes
          .reduce((acc, protocolType) => [...acc, ...Object.keys(protocolMap[protocolType])], [])
          .reduce((acc, poolId) => ({...acc, [poolId]: poolId}), {});

        this.setState({ configurableFields, protocolMap, protocolTypes, newPoolIdMap });
      });
    }
  };

  handleChangeSpreadsheetFile = e => {
    this.setState({ spreadsheetFile: e.target.files[0] });
  };


  // Getting dates from the humancellatlas API, as they are not in the spreadsheet.
  fetchProjectData = async () => {
    const { projectUuid } = this.state;
    const projectUrl = new URL(Config.ingestApiProjectSearch);
    projectUrl.searchParams.append('uuid', projectUuid);

    try {
      const { data } = await axios.get(projectUrl);

      const projectData = {
        submissionDate: moment(data.submissionDate).format("YYYY-MM-DD"),
        lastUpdateDate: moment(data.updateDate).format("YYYY-MM-DD"),
        geoAccessions: data.content.geo_series_accessions || [],
      };

      this.setState({ projectData });
    } catch(e) {
      console.log('could not find that UUID');
      this.setState({ projectData: 'ERROR' });
      return;
    };
  };

  checkErrors = () => this.state.requiredFields.reduce((errors, key) => this.state[key] ? errors : [...errors, key], []);

  poolIdUpdater = () => {
    const { protocolMap, protocolTypes, newPoolIdMap } = this.state;

    this.setState({ newPoolIdMap: calculateNewPoolIds(protocolMap, protocolTypes, newPoolIdMap) });
  };


  render() {
    const {
      handleChangeAccession,
      handleChangeConfigurableField,
      handleChangeCurators,
      handleChangeProjectUuid,
      handleChangeSpreadsheetFile,
      handleClickFetchProjectDetailsAgain,
      handleClickFinishButton,
      handleClickSkipFetchProjectDetails,
      handleClickProcess,
      poolIdUpdater,
      state: { configurableFields, curators, errors, projectUuid, protocolMap, newPoolIdMap, protocolTypes, projectData, processed }
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
              disabled={processed}
              onChange={handleChangeSpreadsheetFile}
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
              disabled={processed}
              onChange={handleChangeAccession}
            />
            {errors.includes('accession') && <p>Enter an accession number for the submission!</p>}
          </div>

          <div>
            <h3>3. Curators</h3>
            <InputList
              type="text"
              source={curators}
              changeHandler={handleChangeCurators}
              processed={processed}
              defaults={['AD', 'JFG']}
            />
            {errors.includes('curators') && <p>Enter at least one curator!</p>}
          </div>

          <div>
            <button
              onClick={handleClickProcess}
              disabled={processed}
            >
              Process!
            </button>
          </div>
        </div>

        {
          !!(protocolTypes.length && projectData === 'ERROR') &&
            <div>
              <h3>Force a Project UUID</h3>
              <p>Could not find the project UUID for that spreadsheet. Enter one</p>
              <input
                type="text"
                source={projectUuid}
                onChange={handleChangeProjectUuid}
              />
              <button
                onClick={handleClickFetchProjectDetailsAgain}
              >
                Fetch again!
              </button>
              <p>or</p>
              <button
                onClick={handleClickSkipFetchProjectDetails}
              >
                Fill in project details manually
              </button>
            </div>
        }

        {
          !!(protocolTypes.length && projectData && projectData !== 'ERROR') &&
          <div>
            <h2>Second part: Protocol matching</h2>
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

            {configurableFields.map(configurableField =>
              <ConfigurableField
                key={configurableField.name}
                changeHandler={handleChangeConfigurableField}
                {...configurableField}
              />
            )}

            <button
              onClick={handleClickFinishButton}
            >
              That looks all right
            </button>
          </div>
        }
      </>
    );
  }
}


export default ConverterApp;
