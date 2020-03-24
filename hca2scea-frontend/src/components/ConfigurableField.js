import React from 'react';


const ConfigurableField = (props) => {
  const fieldName = `${props.name}-field`;

  return (
    <div>
      {props.type && (props.type === 'dropdown' || props.type === 'column') &&
        <>
          <label htmlFor={fieldName}>{props.name}</label>
          <select
            id={fieldName}
            name={props.name}
            value={props.value}
            onChange={props.changeHandler}
          >
            {props.source.map(option =>
              <option
                key={`${option}-${fieldName}`}
                value={option}
              >
                {option}
              </option>
            )}
          </select>
        </>
      }
      {!props.type &&
        <>
          <label htmlFor={fieldName}>{props.name}</label>
          <input
            id={fieldName}
            name={props.name}
            value={props.value}
            onChange={props.changeHandler}
          />
        </>
      }
    </div>
  );
};


export default ConfigurableField;
