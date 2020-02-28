import React from 'react';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faBox, faBoxOpen } from '@fortawesome/free-solid-svg-icons'

import Protocol from './Protocol';



class ProtocolPool extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      dragOver: false,
      newPoolId: undefined,
    };
  }


  handleDragOver = (e) => {
    e.preventDefault();
    this.setState({ dragOver: true });
  };


  handleDragExit = (e) => {
    e.preventDefault();
    this.setState({ dragOver: false });
  };

  handleDrop = (e) => {
    const { moveProtocolHandler, poolId } = this.props;

    const hcaId = e.dataTransfer.getData('hcaId');
    const originatingPoolId = e.dataTransfer.getData('originatingPoolId');

    if (poolId === originatingPoolId) {
      console.log('moved to same pool');
      return;
    }

    moveProtocolHandler(hcaId, originatingPoolId, poolId);

    this.setState({ dragOver: false });
  };

  handleChangeProtocolDescription = (e) => {
    const { poolId, protocols } = this.props;

    this.props.changeProtocolDescriptionHandler(poolId, protocols[0].hcaId, e.target.value);
  };


  render() {
    const {
      handleChangeProtocolDescription,
      props: { poolId, protocols, newPoolId },
      state: { dragOver },
    } = this;

    return (
      <ul
        droppable="1"
        onDragOver={this.handleDragOver}
        onDragLeave={this.handleDragExit}
        onDrop={this.handleDrop}
        onDragEnd={this.handleDragExit}
        className={`${dragOver ? 'drag__over bg-mid' : 'bg-light'} text-center rounded border-dark m-md p-md`}
      >
        <h4 className="text-center my-none py-none mb-xs rounded bg-mid">
          {
            dragOver ? <FontAwesomeIcon className="mx-sm" icon={faBoxOpen} size="1x" />
            :
            <FontAwesomeIcon className="mx-sm" icon={faBox} size="1x" />
          }
          <span className={newPoolId !== poolId ? 'fg-danger text-linethrough' : ''}>{poolId}</span>
          {
            (newPoolId !== '' && newPoolId !== poolId) &&
              <>
                <FontAwesomeIcon className="fg-warning mx-sm" icon={faArrowRight} size="1x" />
                <span className="fg-success">{newPoolId}</span>
              </>
          }
        </h4>
        <div>
          {protocols.map(protocol =>
            <Protocol
              key={`protocol-${protocol.hcaId}`}
              hcaId={protocol.hcaId}
              poolId={protocol.poolId}
              description={protocol.description}
            />
          )}
        </div>
        {
          protocols.length ?
            <textarea
              className="fix-textarea border-dark w-90"
              key={`protocol-description-${protocols[0].hcaId}`}
              value={protocols[0].description}
              rows="5"
              onChange={handleChangeProtocolDescription}
            />
            :
            <p>Empty</p>
        }
      </ul>
    );
  }
}


export default ProtocolPool;
