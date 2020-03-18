import React from 'react';

import ProtocolPool from './ProtocolPool';


class ProtocolMatcher extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      protocolPoolList: Object.keys(this.props.protocolMap),
      protocolPools: this.props.protocolMap,
    };
  }

  changeProtocolHandler = (protocolPool, hcaId, newDescription) => {
    const { protocolPools } = this.state;

    const newProtocolPools = { ...protocolPools };
    const protocolToChange = newProtocolPools[protocolPool].findIndex(protocol => protocol.hcaId === hcaId);

    newProtocolPools[protocolPool][protocolToChange].description = newDescription;

    this.setState({ protocolPools: newProtocolPools });
  };


  moveProtocolHandler = (hcaId, originatingPoolId, destinationPoolId) => {
    const {
      props: { poolIdUpdater },
      state: { protocolPools },
    } = this;

    console.log('protocolPools', protocolPools);
    if (!protocolPools[originatingPoolId]) {
      console.log('Cannot move protocols between types!');
      return;
    }

    // Move protocol from origin poolId to destination poolId, updating its poolId field.
    const protocolToMove = protocolPools[originatingPoolId].find(protocol => protocol.hcaId === hcaId);
    protocolToMove.poolId = destinationPoolId;
    protocolPools[destinationPoolId].push(protocolToMove);
    protocolPools[originatingPoolId] = protocolPools[originatingPoolId].filter(protocol => protocol.hcaId !== hcaId);

    // Calculate newPoolIds for all pools in this matcher.
    poolIdUpdater();

    this.setState({ protocolPools });
  };


  render() {
    const {
      changeProtocolHandler,
      moveProtocolHandler,
      state: { protocolPoolList, protocolPools },
      props: { protocolType, newPoolIdMap }
    } = this;

    return (
      <div className="list-container">
        <h3>{protocolType}</h3>
        <div className="list-container__grid px-lg">
          {protocolPoolList.map(poolId =>
            <ProtocolPool
              key={`protocolpool-${poolId}`}
              poolId={poolId}
              newPoolId={newPoolIdMap[poolId]}
              protocols={protocolPools[poolId]}
              moveProtocolHandler={moveProtocolHandler}
              changeProtocolHandler={changeProtocolHandler}
            />
          )}
        </div>
      </div>
    );
  }
}


export default ProtocolMatcher;
