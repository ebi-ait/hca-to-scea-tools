export const fixProtocolMap = function (protocolMap) {
  const protocolTypes = Object.keys(protocolMap);
  const result = {};

  protocolTypes.forEach(protocolType => {
    result[protocolType] = {};

    Object.keys(protocolMap[protocolType]).forEach(hcaId => {
      const protocol = protocolMap[protocolType][hcaId];
      const { description, scea_id, ...rest } = protocol;
      const poolId = scea_id;

      if (!result[protocolType][poolId]) {
        result[protocolType][poolId] = [];
      }

      const fixedProtocol = {
        description,
        protocolType,
        hcaId,
        poolId,
        ...rest
      }

      result[protocolType][poolId].push(fixedProtocol);
    });
  });

  return result;
};


// This transforms the app's protocolMap to the format needed by the python script:
/* protocol_type: {
 *   protocol_name: {
 *     scea_id: "P-HCADnn-m",
 *     hca_ids: [<LIST OF HCA_IDS THAT MERGE INTO THIS PROTOCOL>],
 *     description: "lorem ipsum...",
 *   }
 * }
 */
export const revertProtocolMap = function (protocolMap, protocolTypes, newPoolIdMap) {
  return protocolTypes.reduce((types, protocolType) => ({
    ...types,
    [protocolType]: Object.keys(protocolMap[protocolType]).reduce((pools, protocolPoolId) => {
      const protocolPool = protocolMap[protocolType][protocolPoolId];
      if (protocolPool.length) {
        const { hcaId, poolId, protocolType, ...rest} = protocolPool[0];

        return {
          ...pools,
          [hcaId]: {
            sceaId: newPoolIdMap[protocolPoolId],
            hcaIds: protocolPool.map(protocol => protocol.hcaId),
            ...rest,
          }
        };
      }

      return pools;
    }, {})
  }), {});
};


const createPoolId = (poolId, poolIdCounter) => `${poolId.match(/P-HCAD\d*/)[0]}-${poolIdCounter}`;


export const calculateNewPoolIds = function (protocolMap, protocolTypes) {
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

  console.log('calculated new pool ids for', protocolMap, protocolTypes, updatedNewPoolIdMap);
  return updatedNewPoolIdMap;
};


const camel2SnakeCase = str => str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);

export const json2Dict = obj => {
  let newObj = {};

  Object.keys(obj).forEach(key => {
    const newKey = camel2SnakeCase(key);
    let value = obj[key];

    if (typeof value === "object" && !Array.isArray(value)) {
      value = json2Dict(value);
    }

    newObj[newKey] = value;
  });

  return newObj;
}
