export const fixProtocolMap = function (protocolMap, protocolTypes) {
  const result = {};

  protocolTypes.forEach(protocolType => {
    result[protocolType] = {};

    Object.keys(protocolMap[protocolType]).forEach(protocol => {
      const poolId = protocolMap[protocolType][protocol].id;

      if (!result[protocolType][poolId]) {
        result[protocolType][poolId] = [];
      }

      result[protocolType][poolId].push({
        protocolType,
        hcaId: protocol,
        description: protocolMap[protocolType][protocol].description,
        poolId,
      });
    });
  });

  return result;
};


const createPoolId = (poolId, poolIdCounter) => `${poolId.match(/P-HCAD\d{2}/)[0]}-${poolIdCounter}`;


export const calculateNewPoolIds = function (protocolMap, protocolTypes, newPoolIdMap) {
  console.log('calculate new pool ids for', protocolMap, protocolTypes, newPoolIdMap);

  const updatedNewPoolIdMap = {};

  let poolIdCounter = 1;
  protocolTypes.forEach(protocolType => {
    Object.keys(protocolMap[protocolType]).forEach(poolId => {
      if (protocolMap[protocolType][poolId].length === 0) {
        updatedNewPoolIdMap[poolId] = '';
      } else {
        updatedNewPoolIdMap[poolId] = createPoolId(poolId, poolIdCounter);
        poolIdCounter++;
      }
    });
  });

  return updatedNewPoolIdMap;
};